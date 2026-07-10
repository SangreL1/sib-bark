from django import forms
from .models import Empleado, LiquidacionSueldo, AFP, ParametroLegal, TablaImpuestoUnico

class EmpleadoForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = [
            'nombre_completo', 'rut', 'direccion', 'cargo', 
            'tipo_contrato', 'fecha_ingreso', 'fecha_termino', 'unidad_negocio',
            'sueldo_base', 'afp', 'sistema_salud', 'isapre_nombre', 'isapre_plan_uf',
            'cuenta_bancaria', 'banco', 'activo'
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Juan Pérez'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-select'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_termino': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'unidad_negocio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. HOSTAL CALAMA'}),
            'sueldo_base': forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
            'afp': forms.Select(attrs={'class': 'form-select'}),
            'sistema_salud': forms.Select(attrs={'class': 'form-select'}),
            'isapre_nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Si aplica'}),
            'isapre_plan_uf': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ej. 2.5'}),
            'cuenta_bancaria': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'N° de Cuenta'}),
            'banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Banco Estado'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class AFPForm(forms.ModelForm):
    class Meta:
        model = AFP
        fields = ['nombre', 'comision_porcentaje']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'comision_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }

class ParametroLegalForm(forms.ModelForm):
    class Meta:
        model = ParametroLegal
        fields = ['nombre', 'valor_moneda']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'valor_moneda': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }

class TablaImpuestoUnicoForm(forms.ModelForm):
    class Meta:
        model = TablaImpuestoUnico
        fields = ['tramo_desde_utm', 'tramo_hasta_utm', 'factor', 'rebaja', 'valor_utm']
        widgets = {
            'tramo_desde_utm': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'tramo_hasta_utm': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'factor': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'step': '0.001'}),
            'rebaja': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            # We'll allow editing UTM globally with JS, so here it's hidden or we just update the first row
            'valor_utm': forms.NumberInput(attrs={'class': 'form-control d-none'}) 
        }

