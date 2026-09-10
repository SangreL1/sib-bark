from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date
from .models import OrdenCompra, Costo, FMR, Entrega

class BarkModelsTestCase(TestCase):
    def setUp(self):
        # Create a test Purchase Order
        self.oc = OrdenCompra.objects.create(
            numero_oc="TEST-OC-12345/ABC-999", # includes a slash to test routing!
            cliente="CLIENTE PRUEBA",
            fecha_oc=date(2026, 1, 1),
            proyecto="Proyecto Piloto",
            descripcion="Fabricación de vigas de soporte",
            valor_total=Decimal("10000000.00"),  # 10 Million
            tiempo_fabricacion=15,
            fecha_compromiso=date(2026, 1, 20),
            estado="En proceso"
        )

    def test_orden_compra_creation(self):
        """Verify the creation and properties of OrdenCompra."""
        self.assertEqual(self.oc.numero_oc, "TEST-OC-12345/ABC-999")
        self.assertEqual(str(self.oc), "TEST-OC-12345/ABC-999 — CLIENTE PRUEBA")
        self.assertEqual(self.oc.valor_total, Decimal("10000000.00"))

    def test_cost_margin_calculations(self):
        """Verify that costs added to the purchase order are aggregated correctly."""
        # Check initial state (no costs)
        costs = self.oc.costos.all()
        self.assertEqual(costs.count(), 0)
        
        # Add a materials cost
        cost1 = Costo.objects.create(
            orden_compra=self.oc,
            categoria="Materiales",
            descripcion="Planchas de acero A36",
            monto=Decimal("4000000.00"),  # 4 Million
            proveedor="Proveedor Metales",
            fecha=date(2026, 1, 5)
        )
        
        # Add a labor cost
        cost2 = Costo.objects.create(
            orden_compra=self.oc,
            categoria="Mano de Obra",
            descripcion="Soldadores calificados",
            monto=Decimal("2500000.00"),  # 2.5 Million
            proveedor="Taller A",
            fecha=date(2026, 1, 10)
        )
        
        # Aggregate costs and verify calculations
        all_costs = self.oc.costos.all()
        self.assertEqual(all_costs.count(), 2)
        
        total_costs = sum(c.monto for c in all_costs)
        self.assertEqual(total_costs, Decimal("6500000.00"))
        
        budget = self.oc.valor_total
        margin = budget - total_costs
        self.assertEqual(margin, Decimal("3500000.00"))
        
        margin_pct = (margin / budget * 100)
        self.assertEqual(margin_pct, Decimal("35.00"))
        
        budget_used_pct = (total_costs / budget * 100)
        self.assertEqual(budget_used_pct, Decimal("65.00"))

    def test_fmr_association(self):
        """Verify that FMR records are properly linked to their OC."""
        fmr = FMR.objects.create(
            fmr_code="FMR-9999",
            orden_compra=self.oc,
            fecha=date(2026, 1, 3),
            cotizacion="COT-500",
            guia_despacho="1250",
            factura="800",
            registro_link="https://drive.google.com/file/d/testlink"
        )
        
        self.assertEqual(fmr.orden_compra, self.oc)
        self.assertEqual(self.oc.fmrs.count(), 1)
        self.assertEqual(self.oc.fmrs.first().fmr_code, "FMR-9999")

    def test_entrega_association(self):
        """Verify that Deliveries are properly linked and logged."""
        delivery = Entrega.objects.create(
            orden_compra=self.oc,
            fecha_entrega=date(2026, 1, 15),
            guia_despacho="1255",
            cantidad_entregada="10 Vigas Tipo A",
            observaciones="ENTREGA COMPLETA",
            estado="Entregado"
        )
        
        self.assertEqual(delivery.orden_compra, self.oc)
        self.assertEqual(self.oc.entregas.count(), 1)
        self.assertEqual(self.oc.entregas.first().guia_despacho, "1255")

    def test_add_cost_view(self):
        """Verify that the add_cost POST view works correctly with nested slashes in OC names."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='testviewer', password='password')
        self.client.force_login(user)

        url = reverse('add_cost', kwargs={'numero_oc': self.oc.numero_oc})
        data = {
            'categoria': 'Materiales',
            'descripcion': 'Planchas Acero Test View',
            'monto': '1500000.00',
            'fecha': '2026-07-03',
            'proveedor': 'Aceros Santiago',
            'documento_referencia': 'Factura Test 123'
        }
        
        response = self.client.post(url, data)
        
        # Verify redirection to project detail
        detail_url = reverse('project_detail', kwargs={'numero_oc': self.oc.numero_oc})
        self.assertRedirects(response, detail_url)
        
        # Verify object creation
        cost = Costo.objects.filter(descripcion='Planchas Acero Test View').first()
        self.assertIsNotNone(cost)
        self.assertEqual(cost.monto, Decimal('1500000.00'))
        self.assertEqual(cost.categoria, 'Materiales')
        self.assertEqual(cost.orden_compra, self.oc)

    def test_trazabilidad_logging(self):
        """Verify that Trazabilidad entry creation works when actions are performed."""
        from django.contrib.auth import get_user_model
        from .views import registrar_trazabilidad
        
        User = get_user_model()
        user = User.objects.create_user(username='testuser', password='password')
        
        # Manually invoke logger
        registrar_trazabilidad(
            orden_compra=self.oc,
            accion="Test Acción",
            detalle="Detalle de prueba para registro",
            usuario=user
        )
        
        from .models import Trazabilidad
        log = Trazabilidad.objects.filter(orden_compra=self.oc, accion="Test Acción").first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.usuario, user)
        self.assertEqual(log.detalle, "Detalle de prueba para registro")

    def test_item_oc_creation(self):
        """Verify ItemOC creation and weight/value properties."""
        from .models import ItemOC
        
        item = ItemOC.objects.create(
            orden_compra=self.oc,
            linea="001",
            codigo="PL-101-A",
            descripcion="Plancha Acero A36 Apernada",
            unidad="EA",
            peso_unitario_kg=Decimal("12.50"),
            cantidad=4,
            precio_unitario=Decimal("50000")
        )
        
        self.assertEqual(item.peso_total_kg, Decimal("50.00"))
        self.assertEqual(item.valor_total, Decimal("200000.00"))
        self.assertEqual(str(item), "001 - Plancha Acero A36 Apernada (PL-101-A)")

    def test_costo_material_model_and_calculations(self):
        """Verify CostoMaterial total calculation."""
        from .models import CostoMaterial
        
        mat = CostoMaterial.objects.create(
            orden_compra=self.oc,
            producto="Estructuras de Prueba",
            cantidad=Decimal("5.50"),
            valor_unitario=Decimal("200000.00"),
            proveedor="Metalúrgica A",
            fecha_compra=date(2026, 7, 5)
        )
        
        self.assertEqual(mat.total, Decimal("1100000.00"))
        self.assertEqual(str(mat), f"Estructuras de Prueba × 5.50 — OC {self.oc.numero_oc}")

    def test_costo_mano_obra_model_and_calculations(self):
        """Verify CostoManoObra calculations including overtimes."""
        from .models import CostoManoObra
        
        # Soldador con 40 hrs normales y 10 extra a precio_hora=10000 con 2 trabajadores
        mo = CostoManoObra.objects.create(
            orden_compra=self.oc,
            cargo="Soldador",
            precio_hora=Decimal("10000.00"),
            horas_normales=Decimal("40.00"),
            horas_extra=Decimal("10.00"),
            cantidad_trabajadores=2
        )
        
        # Horas totales por trabajador = 50.
        self.assertEqual(mo.horas_totales, Decimal("50.00"))
        
        # Total: (40 + 10) * 10000 * 2 = 1.000.000
        self.assertEqual(mo.total, Decimal("1000000.00"))
        self.assertEqual(mo.nombre_cargo, "Soldador")

    def test_add_and_delete_cost_material_views(self):
        """Verify detailed materials creation views."""
        from django.contrib.auth import get_user_model
        from .models import MateriaPrima
        
        User = get_user_model()
        user = User.objects.create_user(username='materialtester', password='password')
        self.client.force_login(user)

        # 1. Test ADD Material
        url_add = reverse('add_cost_material', kwargs={'numero_oc': self.oc.numero_oc})
        data = {
            'producto': 'Tornillos Anclaje 3/4',
            'cantidad': '10',
            'valor_unitario': '1500',
            'total': '15000'
        }
        
        response = self.client.post(url_add, data)
        detail_url = reverse('project_detail', kwargs={'numero_oc': self.oc.numero_oc})
        self.assertRedirects(response, detail_url)
        
        mat = MateriaPrima.objects.filter(producto='Tornillos Anclaje 3/4').first()
        self.assertIsNotNone(mat)
        self.assertEqual(mat.total, Decimal('15000'))
        
        # 2. Test DELETE Material
        url_del = reverse('delete_cost_material', kwargs={'numero_oc': self.oc.numero_oc, 'item_id': mat.id})
        res_del = self.client.get(url_del)
        self.assertRedirects(res_del, detail_url)
        self.assertEqual(MateriaPrima.objects.filter(id=mat.id).count(), 0)

    def test_add_and_delete_cost_mano_obra_views(self):
        """Verify detailed labor creation views."""
        from django.contrib.auth import get_user_model
        from .models import ManoDeObra, Cargo
        
        # Obtener o crear cargo de prueba, forzando precio_hora a 6000
        cargo, _ = Cargo.objects.get_or_create(nombre='Pintor')
        cargo.precio_hora = 6000
        cargo.save()

        User = get_user_model()
        user = User.objects.create_user(username='labortester', password='password')
        self.client.force_login(user)

        # 1. Test ADD Labor
        url_add = reverse('add_cost_mano_obra', kwargs={'numero_oc': self.oc.numero_oc})
        data = {
            'cargo': cargo.id,
            'dias': '2',
            'horas': '15',
            'horas_extra': '2',
            'cantidad_trabajadores': '3'
        }
        
        response = self.client.post(url_add, data)
        detail_url = reverse('project_detail', kwargs={'numero_oc': self.oc.numero_oc})
        self.assertRedirects(response, detail_url)
        
        mo = ManoDeObra.objects.filter(cargo=cargo).first()
        self.assertIsNotNone(mo)
        self.assertEqual(mo.cargo.nombre, 'Pintor')
        # (2 días * 15 horas * 6000) * 3 trabajadores = 540000 base
        # 2 horas extra * 6000 = 12000 extra. Total = 552000
        self.assertEqual(mo.total, Decimal('552000'))

        # 2. Test DELETE Labor
        url_del = reverse('delete_cost_mano_obra', kwargs={'numero_oc': self.oc.numero_oc, 'item_id': mo.id})
        res_del = self.client.get(url_del)
        self.assertRedirects(res_del, detail_url)
        self.assertEqual(ManoDeObra.objects.filter(id=mo.id).count(), 0)

    def test_packing_list_weight_and_edit(self):
        """Verify packing list item creation, weight auto-calculation, editing, and report generation."""
        from django.contrib.auth import get_user_model
        from .models import ItemOC, PackingListItem, PackingList
        
        User = get_user_model()
        user = User.objects.create_user(username='packingtester', password='password')
        self.client.force_login(user)

        # 1. Create item_oc with unit weight
        item_oc = ItemOC.objects.create(
            orden_compra=self.oc,
            linea="001",
            codigo="ITEM-KG-01",
            descripcion="Estructura Metálica A36",
            unidad="EA",
            peso_unitario_kg=Decimal("15.50"),
            cantidad=10,
            precio_unitario=Decimal("100000")
        )

        delivery = Entrega.objects.create(
            orden_compra=self.oc,
            fecha_entrega=date(2026, 8, 1),
            guia_despacho="GD-1001",
            estado="Entregado"
        )

        pl = PackingList.objects.create(
            orden_compra=self.oc,
            entrega=delivery,
            nombre_cliente=self.oc.cliente,
            fecha_orden=date(2026, 8, 1),
            fecha_envio=date(2026, 8, 2)
        )

        # 2. Add packing item without explicit peso_kg -> should auto calculate 15.50 * 2 = 31.00 kg
        url_add_pi = reverse('add_packing_item', kwargs={'numero_oc': self.oc.numero_oc, 'entrega_id': delivery.id})
        data_add = {
            'item_oc': item_oc.id,
            'cantidad': '2',
            'numero_bulto': 'PALLET-01'
        }
        res_add = self.client.post(url_add_pi, data_add)
        self.assertEqual(res_add.status_code, 302)

        pi = PackingListItem.objects.filter(entrega=delivery).first()
        self.assertIsNotNone(pi)
        self.assertEqual(pi.peso_kg, Decimal("31.00"))

        # 3. Edit packing item -> change peso_kg manually to 35.50
        url_edit_pi = reverse('edit_packing_item', kwargs={'numero_oc': self.oc.numero_oc, 'item_id': pi.id})
        data_edit = {
            'item_oc': item_oc.id,
            'cantidad': '2',
            'numero_bulto': 'PALLET-01-EDIT',
            'peso_kg': '35.50',
            'diametro': 'DN50',
            'estado_item': 'ENTREGADO'
        }
        res_edit = self.client.post(url_edit_pi, data_edit)
        self.assertEqual(res_edit.status_code, 302)

        pi.refresh_from_db()
        self.assertEqual(pi.peso_kg, Decimal("35.50"))
        self.assertEqual(pi.numero_bulto, 'PALLET-01-EDIT')

        # 4. Export PDF & Excel report testing
        url_pdf = reverse('generate_packing_list_pdf', kwargs={'packing_list_id': pl.id})
        res_pdf = self.client.get(url_pdf)
        self.assertEqual(res_pdf.status_code, 200)
        self.assertEqual(res_pdf['Content-Type'], 'application/pdf')

        url_excel = reverse('export_packing_list_excel', kwargs={'packing_list_id': pl.id})
        res_excel = self.client.get(url_excel)
        self.assertEqual(res_excel.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', res_excel['Content-Type'])


class UsuariosYRUTTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='superadmin',
            email='admin@bark.cl',
            password='Password123!',
            first_name='Admin',
            last_name='11.111.111-1'
        )
        self.empleado = User.objects.create_user(
            username='151234567',
            email='empleado@bark.cl',
            password='Password123!',
            first_name='Carlos',
            last_name='15.123.456-7',
            is_staff=True,
            is_active=True
        )

    def test_login_con_rut_varios_formatos(self):
        # 1. Login con RUT formateado con puntos y guion
        res = self.client.post(reverse('login'), {
            'username': '15.123.456-7',
            'password': 'Password123!'
        })
        self.assertEqual(res.status_code, 302)
        self.client.logout()

        # 2. Login con RUT sin puntos
        res = self.client.post(reverse('login'), {
            'username': '15123456-7',
            'password': 'Password123!'
        })
        self.assertEqual(res.status_code, 302)
        self.client.logout()

        # 3. Login con RUT sin guion ni puntos
        res = self.client.post(reverse('login'), {
            'username': '151234567',
            'password': 'Password123!'
        })
        self.assertEqual(res.status_code, 302)
        self.client.logout()

        # 4. Login con fallback username clásico (superadmin)
        res = self.client.post(reverse('login'), {
            'username': 'superadmin',
            'password': 'Password123!'
        })
        self.assertEqual(res.status_code, 302)

    def test_crear_y_eliminar_staff_sin_error_404(self):
        self.client.login(username='superadmin', password='Password123!')

        # Crear nuevo empleado desde el panel
        res_crear = self.client.post(reverse('crear_staff'), {
            'nombre': 'Esteban Morales',
            'rut': '16.234.567-2',
            'email': 'esteban@bark.cl',
            'password': 'SecurePassword123!',
            'rol': 'staff'
        })
        self.assertEqual(res_crear.status_code, 302)
        nuevo_user = User.objects.filter(last_name='16.234.567-2').first()
        self.assertIsNotNone(nuevo_user)
        self.assertTrue(nuevo_user.is_staff)
        self.assertTrue(nuevo_user.is_active)

        # Eliminar el empleado vía POST (no debe dar 404 ni bucle de redirección)
        res_eliminar = self.client.post(reverse('eliminar_staff', kwargs={'user_id': nuevo_user.id}))
        self.assertEqual(res_eliminar.status_code, 302)
        self.assertFalse(User.objects.filter(id=nuevo_user.id).exists())

        # Probar que una petición posterior a esa URL no arroje 404
        res_repetido = self.client.get(reverse('eliminar_staff', kwargs={'user_id': nuevo_user.id}))
        self.assertEqual(res_repetido.status_code, 302)

    def test_respaldos_factura_y_guia_orden_compra(self):
        oc = OrdenCompra.objects.create(
            numero_oc="OC-TEST-RESPALDOS-001",
            cliente="Minera Escondida",
            valor_total=Decimal("5000000"),
            factura_link="https://drive.google.com/factura/123",
            guia_link="https://drive.google.com/guia/456"
        )
        self.assertEqual(oc.factura_link, "https://drive.google.com/factura/123")
        self.assertEqual(oc.guia_link, "https://drive.google.com/guia/456")



