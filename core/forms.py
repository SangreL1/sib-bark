from django import forms
from .models import (
    OrdenCompra, FMR, Entrega, Costo, ItemOC, Trazabilidad, PackingListItem,
    Factura, CostoMaterial, CostoManoObra, Cotizacion, ItemCotizacion,
    GuiaDespacho, ItemGuia,
)


class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = [
            'numero_oc', 'cliente', 'proyecto', 'descripcion',
            'fecha_oc', 'fecha_compromiso', 'tiempo_fabricacion',
            'valor_total', 'estado', 'prioridad', 'peso_total_manual',
            'guia_despacho_resumen', 'factura_resumen', 'fecha_factura',
            'observaciones',
            'oc_link', 'oc_file',
            'plano_link', 'plano_file',
            'cotizacion_link', 'cotizacion_file',
            'excel_link', 'excel_file',
            'dossier_link', 'dossier_file',
            'fmr_link', 'fmr_file',
        ]
        widgets = {
            'numero_oc': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. D3MC - F-2-03528-FLD-01/D3MC104397'}),
            'cliente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del cliente'}),
            'proyecto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre o código del proyecto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción del trabajo a realizar'}),
            'fecha_oc': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_compromiso': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'tiempo_fabricacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Días hábiles'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'guia_despacho_resumen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° de guías emitidas'}),
            'factura_resumen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° de factura'}),
            'fecha_factura': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'peso_total_manual': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Kg total (Opcional/Legacy)', 'step': '0.01'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notas adicionales'}),
            
            # URLs
            'oc_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'plano_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'cotizacion_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'excel_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'dossier_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            'fmr_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://drive.google.com/...'}),
            
            # Files
            'oc_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'plano_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'cotizacion_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'excel_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'dossier_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'fmr_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'numero_oc': 'Número de OC',
            'valor_total': 'Valor Total (SIN IVA)',
            'tiempo_fabricacion': 'Tiempo de Fabricación (días hábiles)',
            'oc_file': 'Subir OC (PDF)',
            'plano_file': 'Subir Planos (PDF/DWG)',
            'cotizacion_file': 'Subir Cotización (PDF)',
            'excel_file': 'Subir Excel',
            'dossier_file': 'Subir Dossier de Calidad',
            'fmr_file': 'Subir FMR Adjunto',
        }




class OrdenCompraEditForm(forms.ModelForm):
    """Same as OrdenCompraForm but numero_oc is read-only."""
    class Meta(OrdenCompraForm.Meta):
        fields = [f for f in OrdenCompraForm.Meta.fields if f != 'numero_oc']




class FMRForm(forms.ModelForm):
    class Meta:
        model = FMR
        fields = ['fmr_code', 'fecha', 'cotizacion', 'guia_despacho', 'factura', 'registro_link', 'registro_file']
        widgets = {
            'fmr_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 3528'}),
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'cotizacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° Cotización'}),
            'guia_despacho': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° Guía(s)'}),
            'factura': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° Factura'}),
            'registro_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Link PDF Registro Final (Drive)'}),
            'registro_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'registro_file': 'Subir Registro Final en PDF',
        }


class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ['fecha_entrega', 'guia_despacho', 'guia_file', 'cantidad_entregada', 'estado', 'observaciones']
        widgets = {
            'fecha_entrega': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'guia_despacho': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° Guía de Despacho'}),
            'guia_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'cantidad_entregada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalle de items entregados'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observaciones opcionales'}),
        }
        labels = {
            'guia_file': 'Subir PDF del despacho / guía firmada',
        }


class CostoForm(forms.ModelForm):
    class Meta:
        model = Costo
        fields = ['categoria', 'descripcion', 'monto', 'proveedor', 'fecha', 'documento_referencia']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Planchas de acero A36'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Aceros Chile S.A.'}),
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Factura 4122'}),
        }


class ItemOCForm(forms.ModelForm):
    class Meta:
        model = ItemOC
        fields = [
            'linea', 'item_code', 'size_code', 'descripcion', 'codigo',
            'unidad', 'peso_unitario_kg', 'cantidad', 'cantidad_entregada', 'precio_unitario'
        ]
        widgets = {
            'linea': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Línea'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cód. Ítem'}),
            'descripcion':  forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Soporte SP-1, Brida, Codo 90°'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1',
                'step': '0.01'
            }),
            'size_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 6 IN, 200x35.9, 2" SCH40'
            }),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código Plano'}),
            'unidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'U.M.'}),
            'peso_unitario_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.001'
            }),
            'cantidad_entregada': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'step': '0.01'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
        }
        labels = {
            'linea': 'Línea',
            'item_code': 'Cód. Ítem',
            'descripcion': 'Marca (Nombre de la Pieza)',
            'cantidad': 'Cantidad',
            'size_code': 'Medidas',
            'codigo': 'Código Plano',
            'unidad': 'U.M.',
            'peso_unitario_kg': 'Masa Unit. (kg)',
            'cantidad_entregada': 'Entregado',
            'precio_unitario': 'Precio Unitario ($)',
        }


class PackingListItemForm(forms.ModelForm):
    class Meta:
        model = PackingListItem
        fields = [
            'item_oc', 'cantidad', 'numero_bulto',
            'largo_mt', 'ancho_mt', 'alto_mt', 'peso_kg',
            'modelo_soporte', 'medida_1', 'medida_2',
            'diametro', 'alto_item', 'estado_item', 'unidades',
        ]
        widgets = {
            'item_oc': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cant. despachada'}),
            'numero_bulto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. PALLET 001'}),
            'largo_mt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Largo mt', 'step': '0.01'}),
            'ancho_mt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ancho mt', 'step': '0.01'}),
            'alto_mt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Alto mt', 'step': '0.01'}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso kg', 'step': '0.01'}),
            'modelo_soporte': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. SPS-100'}),
            'medida_1': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ø o L', 'step': '0.001'}),
            'medida_2': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Alto o H', 'step': '0.001'}),
            'diametro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Diámetro / Ø (texto)'}),
            'alto_item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Alto (texto)'}),
            'estado_item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado'}),
            'unidades': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidades'}),
        }
        labels = {
            'medida_1': 'Medida 1 (Ø o L)',
            'medida_2': 'Medida 2 (Alto o H)',
        }

    def __init__(self, *args, **kwargs):
        orden_compra = kwargs.pop('orden_compra', None)
        super().__init__(*args, **kwargs)
        if orden_compra:
            self.fields['item_oc'].queryset = ItemOC.objects.filter(orden_compra=orden_compra)


class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['numero_factura', 'fecha_emision', 'monto', 'estado', 'entrega', 'url_externa', 'archivo']
        widgets = {
            'numero_factura': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 004521'}),
            'fecha_emision':  forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'monto':          forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'estado':         forms.Select(attrs={'class': 'form-control'}),
            'entrega':        forms.Select(attrs={'class': 'form-control'}),
            'url_externa':    forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Link Drive/SharePoint'}),
            'archivo':        forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'archivo': 'Subir PDF de Factura',
        }

    def __init__(self, *args, **kwargs):
        orden_compra = kwargs.pop('orden_compra', None)
        super().__init__(*args, **kwargs)
        if orden_compra:
            # Filtra el selector de Entrega a las entregas de esta OC
            self.fields['entrega'].queryset = Entrega.objects.filter(orden_compra=orden_compra)
            self.fields['entrega'].required = False


class CostoMaterialForm(forms.ModelForm):
    class Meta:
        model  = CostoMaterial
        fields = ['producto', 'cantidad', 'valor_unitario', 'proveedor', 'fecha_compra', 'observaciones']
        widgets = {
            'producto':       forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Planchas acero, Oxígeno, Pintura'}),
            'cantidad':       forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1', 'step': '0.01'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'step': '1'}),
            'proveedor':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Proveedor (opcional)'}),
            'fecha_compra':   forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'observaciones':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Observaciones (opcional)'}),
        }


class CostoManoObraForm(forms.ModelForm):
    class Meta:
        model  = CostoManoObra
        fields = ['cargo', 'cargo_otro', 'precio_hora', 'horas_normales', 'horas_extra', 'cantidad_trabajadores']
        widgets = {
            'cargo':                 forms.Select(attrs={'class': 'form-control'}),
            'cargo_otro':            forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Especificar cargo'}),
            'precio_hora':           forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '3000', 'step': '100'}),
            'horas_normales':        forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '55', 'step': '0.5'}),
            'horas_extra':           forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'step': '0.5'}),
            'cantidad_trabajadores': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1', 'step': '1'}),
        }
        labels = {
            'cargo_otro':            'Nombre del cargo (si eligió "Otro")',
            'precio_hora':           'Precio por hora ($)',
            'horas_normales':        'Horas normales',
            'horas_extra':           'Horas extra',
            'cantidad_trabajadores': 'N° trabajadores',
        }


from .models import Cargo, ManoDeObra, MateriaPrima, PackingList

class MateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = MateriaPrima
        fields = ['producto', 'cantidad', 'valor_unitario', 'total']
        widgets = {
            'producto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Gasto general, Acero A36'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cantidad (opcional)'}),
            'valor_unitario': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Unitario'}),
            'total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Fijar total directo (opcional)'}),
        }


class ManoDeObraForm(forms.ModelForm):
    class Meta:
        model = ManoDeObra
        fields = ['cargo', 'dias', 'horas', 'cantidad_trabajadores', 'horas_extra']
        widgets = {
            'cargo': forms.Select(attrs={'class': 'form-control'}),
            'dias': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Días', 'min': 1}),
            'horas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Horas', 'min': 1}),
            'cantidad_trabajadores': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'N° trabajadores', 'min': 1}),
            'horas_extra': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Horas extra', 'min': 0}),
        }


class PackingListForm(forms.ModelForm):
    class Meta:
        model = PackingList
        fields = ['fecha_orden', 'fecha_envio', 'nombre_cliente', 'empresa', 'direccion', 'correo', 'telefono', 'tipo_medida']
        widgets = {
            'fecha_orden': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_envio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_medida': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'tipo_medida': 'Formato de Columnas de Medida',
        }


# ── Cotización ──────────────────────────────────────────────────────────────

class CotizacionForm(forms.ModelForm):
    class Meta:
        model = Cotizacion
        fields = [
            'fecha', 'valido_hasta', 'cliente_id', 'contacto_nombre', 'contacto_cargo',
            'orden_compra', 'razon_social', 'giro', 'rut_receptor', 'direccion_receptor',
            'ciudad_receptor', 'observaciones',
        ]
        widgets = {
            'fecha': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'valido_hasta': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'cliente_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 1068'}),
            'contacto_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sr. Javier Palma'}),
            'contacto_cargo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cargo del contacto'}),
            'orden_compra': forms.Select(attrs={'class': 'form-control'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón Social del cliente'}),
            'giro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Giro'}),
            'rut_receptor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}),
            'direccion_receptor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'ciudad_receptor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales'}),
        }
        labels = {
            'orden_compra': 'Orden de Compra (opcional)',
            'razon_social': 'Razón Social',
            'rut_receptor': 'RUT',
            'direccion_receptor': 'Dirección',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['orden_compra'].required = False


class ItemCotizacionForm(forms.ModelForm):
    class Meta:
        model = ItemCotizacion
        fields = ['descripcion', 'observacion', 'valor_kg', 'cantidad', 'kg_por_unidad']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Fabricación de Estructura'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Detalle / observación'}),
            'valor_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'step': '1'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1', 'min': '1'}),
            'kg_por_unidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.000', 'step': '0.001'}),
        }
        labels = {
            'valor_kg': 'Valor por kg ($)',
            'kg_por_unidad': 'kg por Unidad',
        }


# ── Guía de Despacho ─────────────────────────────────────────────────────────

class GuiaDespachoForm(forms.ModelForm):
    class Meta:
        model = GuiaDespacho
        fields = [
            'numero_guia', 'fecha_emision',
            'receptor_nombre', 'receptor_rut', 'receptor_giro',
            'receptor_direccion', 'receptor_comuna', 'contacto',
            'tipo_despacho', 'tipo_traslado',
            'chofer_nombre', 'chofer_rut', 'patente', 'transportista_rut',
            'direccion_destino',
        ]
        widgets = {
            'numero_guia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 1556'}),
            'fecha_emision': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'receptor_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razón Social'}),
            'receptor_rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}),
            'receptor_giro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Giro'}),
            'receptor_direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'receptor_comuna': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comuna'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Persona que recibe'}),
            'tipo_despacho': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Sin flete'}),
            'tipo_traslado': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Operación propia'}),
            'chofer_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre del chofer'}),
            'chofer_rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT chofer'}),
            'patente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patente'}),
            'transportista_rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT transportista'}),
            'direccion_destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección de destino'}),
        }
        labels = {
            'numero_guia': 'N° Guía de Despacho',
            'receptor_nombre': 'Razón Social Receptor',
        }


class ItemGuiaForm(forms.ModelForm):
    class Meta:
        model = ItemGuia
        fields = ['descripcion', 'cantidad_unidad', 'precio_unitario']
        widgets = {
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descripción del artículo'}),
            'cantidad_unidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 5 UN'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'step': '1'}),
        }
        labels = {
            'cantidad_unidad': 'Cantidad y Unidad',
            'precio_unitario': 'Precio Unitario ($)',
        }
