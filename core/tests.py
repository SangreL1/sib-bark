from django.test import TestCase
from django.urls import reverse
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
        from .models import CostoMaterial
        
        User = get_user_model()
        user = User.objects.create_user(username='materialtester', password='password')
        self.client.force_login(user)

        # 1. Test ADD Material
        url_add = reverse('add_cost_material', kwargs={'numero_oc': self.oc.numero_oc})
        data = {
            'producto': 'Tornillos Anclaje 3/4',
            'cantidad': '10',
            'valor_unitario': '1500',
            'proveedor': 'Ferretería Industrial',
            'fecha_compra': '2026-07-06'
        }
        
        response = self.client.post(url_add, data)
        detail_url = reverse('project_detail', kwargs={'numero_oc': self.oc.numero_oc})
        self.assertRedirects(response, detail_url)
        
        mat = CostoMaterial.objects.filter(producto='Tornillos Anclaje 3/4').first()
        self.assertIsNotNone(mat)
        self.assertEqual(mat.total, Decimal('15000'))
        
        # 2. Test DELETE Material
        url_del = reverse('delete_cost_material', kwargs={'numero_oc': self.oc.numero_oc, 'item_id': mat.id})
        res_del = self.client.get(url_del)
        self.assertRedirects(res_del, detail_url)
        self.assertEqual(CostoMaterial.objects.filter(id=mat.id).count(), 0)

    def test_add_and_delete_cost_mano_obra_views(self):
        """Verify detailed labor creation views."""
        from django.contrib.auth import get_user_model
        from .models import CostoManoObra
        
        User = get_user_model()
        user = User.objects.create_user(username='labortester', password='password')
        self.client.force_login(user)

        # 1. Test ADD Labor
        url_add = reverse('add_cost_mano_obra', kwargs={'numero_oc': self.oc.numero_oc})
        data = {
            'cargo': 'Pintor',
            'precio_hora': '6000',
            'horas_normales': '30',
            'horas_extra': '2',
            'cantidad_trabajadores': '3'
        }
        
        response = self.client.post(url_add, data)
        detail_url = reverse('project_detail', kwargs={'numero_oc': self.oc.numero_oc})
        self.assertRedirects(response, detail_url)
        
        mo = CostoManoObra.objects.filter(cargo='Pintor').first()
        self.assertIsNotNone(mo)
        self.assertEqual(mo.nombre_cargo, 'Pintor')
        # (30h normal + 2h extra) * 6000 * 3 = 576000
        self.assertEqual(mo.total, Decimal('576000'))

        # 2. Test DELETE Labor
        url_del = reverse('delete_cost_mano_obra', kwargs={'numero_oc': self.oc.numero_oc, 'item_id': mo.id})
        res_del = self.client.get(url_del)
        self.assertRedirects(res_del, detail_url)
        self.assertEqual(CostoManoObra.objects.filter(id=mo.id).count(), 0)

