from django import forms
from .models import OrdenCompra, FMR, Entrega, Costo, ItemOC, Trazabilidad, PackingListItem, Factura, CostoMaterial, CostoManoObra


class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = [
            'numero_oc', 'cliente', 'proyecto', 'descripcion',
            'fecha_oc', 'fecha_compromiso', 'tiempo_fabricacion',
            'valor_total', 'estado', 'prioridad',
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
            'fecha_oc': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_compromiso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tiempo_fabricacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Días hábiles'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'guia_despacho_resumen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° de guías emitidas'}),
            'factura_resumen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° de factura'}),
            'fecha_factura': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
            'fecha_entrega': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'documento_referencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Factura 4122'}),
        }


class ItemOCForm(forms.ModelForm):
    class Meta:
        model = ItemOC
        fields = ['linea', 'codigo', 'descripcion', 'unidad', 'cantidad', 'peso_unitario_kg', 'precio_unitario', 'cantidad_entregada']
        widgets = {
            'linea': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 0001'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 1332SSK00402-SP00001'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Soporte SP-1'}),
            'unidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. EA o KG'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1'}),
            'peso_unitario_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Masa en kg (opcional)'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Moneda base'}),
            'cantidad_entregada': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}),
        }


class PackingListItemForm(forms.ModelForm):
    class Meta:
        model = PackingListItem
        fields = ['item_oc', 'cantidad', 'numero_bulto', 'largo_mt', 'ancho_mt', 'alto_mt', 'peso_kg']
        widgets = {
            'item_oc': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Cant. despachada'}),
            'numero_bulto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. PALLET 001'}),
            'largo_mt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Largo mt', 'step': '0.01'}),
            'ancho_mt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ancho mt', 'step': '0.01'}),
            'alto_mt': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Alto mt', 'step': '0.01'}),
            'peso_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso kg', 'step': '0.01'}),
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
            'fecha_emision':  forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
            'fecha_compra':   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
