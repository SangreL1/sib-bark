import os
import math
import pandas as pd
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import OrdenCompra, FMR, Entrega

class Command(BaseCommand):
    help = 'Seeds database with historical data from Bark Excel sheets.'

    def handle(self, *args, **options):
        self.stdout.write("Starting data seeding process...")

        # Paths to Excel files
        control_oc_path = r"c:\Users\Coalfa\Desktop\FLUOR\Control_Ordenes_Compra_Maestranza.xlsx"
        fluor_fmr_path = r"c:\Users\Coalfa\Desktop\FLUOR\FLUOR FMR.xlsx"

        if not os.path.exists(control_oc_path):
            self.stderr.write(f"Error: Could not find Control OC sheet at {control_oc_path}")
            return
        if not os.path.exists(fluor_fmr_path):
            self.stderr.write(f"Error: Could not find FLUOR FMR sheet at {fluor_fmr_path}")
            return

        # ----------------------------------------------------
        # 1. Clear existing database tables
        # ----------------------------------------------------
        self.stdout.write("Clearing existing records...")
        Entrega.objects.all().delete()
        FMR.objects.all().delete()
        OrdenCompra.objects.all().delete()

        # Helpers
        def clean_val(val, default=""):
            if pd.isna(val) or val is None:
                return default
            if isinstance(val, str):
                return val.strip()
            return str(val)

        def clean_decimal(val):
            if pd.isna(val) or val is None:
                return None
            try:
                s = str(val).replace("$", "").replace(" ", "").replace(",", "")
                return float(s)
            except ValueError:
                return None

        def clean_int(val):
            if pd.isna(val) or val is None:
                return None
            try:
                return int(float(val))
            except ValueError:
                return None

        def clean_date(val):
            if pd.isna(val) or val is None:
                return None
            if isinstance(val, datetime):
                return val.date()
            if isinstance(val, pd.Timestamp):
                return val.date()
            try:
                s = str(val).strip()
                if not s or s.lower() == 'nan':
                    return None
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except ValueError:
                        continue
                return None
            except Exception:
                return None

        # ----------------------------------------------------
        # 2. Seed Control OC sheet
        # ----------------------------------------------------
        self.stdout.write("Parsing Control_Ordenes_Compra_Maestranza.xlsx -> Control OC sheet...")
        try:
            df_oc = pd.read_excel(control_oc_path, sheet_name="Control OC")
        except Exception as e:
            self.stderr.write(f"Failed to load 'Control OC' sheet: {e}")
            return

        # Normalize column names robustly
        col_map = {}
        for c in df_oc.columns:
            c_clean = str(c).strip().upper().replace(' ', '').replace('\ufffd', '')
            if 'N' in c_clean and 'OC' in c_clean:
                col_map[c] = 'N_OC'
            elif 'CLIENTE' in c_clean:
                col_map[c] = 'CLIENTE'
            elif 'FECHA' in c_clean and 'OC' in c_clean:
                col_map[c] = 'FECHA_OC'
            elif 'PROYECTO' in c_clean:
                col_map[c] = 'PROYECTO'
            elif 'DESCRIP' in c_clean:
                col_map[c] = 'DESCRIPCION'
            elif 'VALOR' in c_clean:
                col_map[c] = 'VALOR_TOTAL'
            elif 'TIEMPO' in c_clean:
                col_map[c] = 'TIEMPO_FABRICACION'
            elif 'COMPROMISO' in c_clean:
                col_map[c] = 'FECHA_COMPROMISO'
            elif 'ESTADO' in c_clean:
                col_map[c] = 'ESTADO'
            elif 'PORCENTAJE' in c_clean or '%' in c_clean:
                col_map[c] = 'PORCENTAJE_ENTREGADO'
            elif 'ULTIMA' in c_clean or 'LTIMA' in c_clean:
                col_map[c] = 'FECHA_ULTIMA_ENTREGA'
            elif 'RESTANTES' in c_clean:
                col_map[c] = 'DIAS_RESTANTES'
            elif 'PRIORIDAD' in c_clean:
                col_map[c] = 'PRIORIDAD'
            elif 'GU' in c_clean and 'DESPACHO' in c_clean:
                col_map[c] = 'GUIA_DESPACHO_RESUMEN'
            elif 'FACTURA' in c_clean and 'FECHA' in c_clean:
                col_map[c] = 'FECHA_FACTURA'
            elif 'FACTURA' in c_clean:
                col_map[c] = 'FACTURA_RESUMEN'
            elif 'OBSERVACION' in c_clean:
                col_map[c] = 'OBSERVACIONES'
            elif c_clean == 'OC':
                col_map[c] = 'OC_LINK'
            elif c_clean == 'FMR':
                col_map[c] = 'FMR_LINK'
            elif c_clean == 'PLANO':
                col_map[c] = 'PLANO_LINK'
            elif c_clean == 'EXCEL':
                col_map[c] = 'EXCEL_LINK'
            elif c_clean == 'DOSSIER':
                col_map[c] = 'DOSSIER_LINK'

        df_oc.rename(columns=col_map, inplace=True)

        created_ocs = 0
        for index, row in df_oc.iterrows():
            oc_num = clean_val(row.get("N_OC"))
            if not oc_num or oc_num.lower() == 'nan':
                continue

            cliente = clean_val(row.get("CLIENTE"), default="Desconocido")
            fecha_oc = clean_date(row.get("FECHA_OC"))
            proyecto = clean_val(row.get("PROYECTO"))
            descripcion = clean_val(row.get("DESCRIPCION"))
            valor_total = clean_decimal(row.get("VALOR_TOTAL"))
            tiempo_fabricacion = clean_int(row.get("TIEMPO_FABRICACION"))
            fecha_compromiso = clean_date(row.get("FECHA_COMPROMISO"))
            estado = clean_val(row.get("ESTADO"), default="En proceso")
            
            # Format percentage (e.g. 1.0 becomes 100.00%)
            pct_val = row.get("PORCENTAJE_ENTREGADO")
            if pd.isna(pct_val) or pct_val is None:
                porcentaje_entregado = 0.0
            else:
                try:
                    pct_val = float(pct_val)
                    if pct_val <= 1.0:
                        porcentaje_entregado = pct_val * 100.0
                    else:
                        porcentaje_entregado = pct_val
                except ValueError:
                    porcentaje_entregado = 0.0

            fecha_ultima_entrega = clean_date(row.get("FECHA_ULTIMA_ENTREGA"))
            dias_restantes = clean_int(row.get("DIAS_RESTANTES"))
            prioridad = clean_val(row.get("PRIORIDAD"))
            guia_despacho_resumen = clean_val(row.get("GUIA_DESPACHO_RESUMEN"))
            factura_resumen = clean_val(row.get("FACTURA_RESUMEN"))
            fecha_factura = clean_date(row.get("FECHA_FACTURA"))
            observaciones = clean_val(row.get("OBSERVACIONES"))

            # Links
            oc_link = clean_val(row.get("OC_LINK"))
            fmr_link = clean_val(row.get("FMR_LINK"))
            plano_link = clean_val(row.get("PLANO_LINK"))
            excel_link = clean_val(row.get("EXCEL_LINK"))
            dossier_link = clean_val(row.get("DOSSIER_LINK"))

            # Create the record
            OrdenCompra.objects.create(
                numero_oc=oc_num,
                cliente=cliente,
                fecha_oc=fecha_oc,
                proyecto=proyecto,
                descripcion=descripcion,
                valor_total=valor_total,
                tiempo_fabricacion=tiempo_fabricacion,
                fecha_compromiso=fecha_compromiso,
                estado=estado,
                porcentaje_entregado=porcentaje_entregado,
                fecha_ultima_entrega=fecha_ultima_entrega,
                dias_restantes=dias_restantes,
                prioridad=prioridad,
                guia_despacho_resumen=guia_despacho_resumen,
                factura_resumen=factura_resumen,
                fecha_factura=fecha_factura,
                observaciones=observaciones,
                oc_link=oc_link if oc_link.startswith("http") else None,
                fmr_link=fmr_link if fmr_link.startswith("http") else None,
                plano_link=plano_link if plano_link.startswith("http") else None,
                excel_link=excel_link if excel_link.startswith("http") else None,
                dossier_link=dossier_link if dossier_link.startswith("http") else None,
            )
            created_ocs += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_ocs} Purchase Orders."))

        # ----------------------------------------------------
        # 3. Seed Entregas sheet
        # ----------------------------------------------------
        self.stdout.write("Parsing Control_Ordenes_Compra_Maestranza.xlsx -> Entregas sheet...")
        try:
            df_entregas = pd.read_excel(control_oc_path, sheet_name="Entregas")
        except Exception as e:
            self.stderr.write(f"Failed to load 'Entregas' sheet: {e}")
            return

        col_map_entregas = {}
        for c in df_entregas.columns:
            c_clean = str(c).strip().upper().replace(' ', '').replace('\ufffd', '')
            if 'N' in c_clean and 'OC' in c_clean:
                col_map_entregas[c] = 'N_OC'
            elif 'FECHA' in c_clean:
                col_map_entregas[c] = 'FECHA_ENTREGA'
            elif 'GU' in c_clean:
                col_map_entregas[c] = 'GUIA_DESPACHO'
            elif 'CANTIDAD' in c_clean:
                col_map_entregas[c] = 'CANTIDAD_ENTREGADA'
            elif 'OBSERVACION' in c_clean:
                col_map_entregas[c] = 'OBSERVACIONES'
            elif 'ESTADO' in c_clean:
                col_map_entregas[c] = 'ESTADO'

        df_entregas.rename(columns=col_map_entregas, inplace=True)

        created_entregas = 0
        for index, row in df_entregas.iterrows():
            oc_num = clean_val(row.get("N_OC"))
            if not oc_num or oc_num.lower() == 'nan':
                continue

            # Check if this OC exists
            try:
                oc = OrdenCompra.objects.get(numero_oc=oc_num)
            except OrdenCompra.DoesNotExist:
                # Try partial match or create a skeleton one
                self.stdout.write(f"Warning: OC '{oc_num}' in Entregas sheet not found in Control OC. Creating skeleton OC.")
                oc = OrdenCompra.objects.create(
                    numero_oc=oc_num,
                    cliente="FLUOR SALFA LTDA" if "D3MC" in oc_num or "FMR" in oc_num else "Desconocido",
                    descripcion="Creado automáticamente desde registro de Entregas"
                )

            fecha_entrega = clean_date(row.get("FECHA_ENTREGA"))
            guia_despacho = clean_val(row.get("GUIA_DESPACHO"))
            cantidad_entregada = clean_val(row.get("CANTIDAD_ENTREGADA"))
            observaciones = clean_val(row.get("OBSERVACIONES"))
            
            raw_estado = clean_val(row.get("ESTADO")).upper()
            if 'INCOMPLETA' in raw_estado:
                estado = 'INCOMPLETA'
            elif 'FACTURADO' in raw_estado:
                estado = 'FACTURADO'
            else:
                estado = 'COMPLETA'

            Entrega.objects.create(
                orden_compra=oc,
                fecha_entrega=fecha_entrega,
                guia_despacho=guia_despacho,
                cantidad_entregada=cantidad_entregada,
                observaciones=observaciones,
                estado=estado
            )
            created_entregas += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_entregas} Delivery Logs."))

        # ----------------------------------------------------
        # 4. Seed FLUOR FMR sheet
        # ----------------------------------------------------
        self.stdout.write("Parsing FLUOR FMR.xlsx -> Hoja1 sheet...")
        try:
            df_fmr = pd.read_excel(fluor_fmr_path, sheet_name="Hoja1", header=3)
        except Exception as e:
            self.stderr.write(f"Failed to load FLUOR FMR 'Hoja1': {e}")
            return

        col_map_fmr = {}
        for c in df_fmr.columns:
            c_clean = str(c).strip().upper().replace(' ', '').replace('\ufffd', '')
            if c_clean == 'FMR':
                col_map_fmr[c] = 'FMR_CODE'
            elif 'FECHA' in c_clean:
                col_map_fmr[c] = 'FECHA'
            elif 'COTIZACION' in c_clean or 'COTIZACI' in c_clean:
                col_map_fmr[c] = 'COTIZACION'
            elif 'ORDEN' in c_clean or 'COMPRA' in c_clean or 'OC' in c_clean:
                col_map_fmr[c] = 'N_OC'
            elif 'GUIA' in c_clean or 'GUA' in c_clean:
                col_map_fmr[c] = 'GUIA_DESPACHO'
            elif 'FACTURA' in c_clean:
                col_map_fmr[c] = 'FACTURA'
            elif 'REGISTRO' in c_clean:
                col_map_fmr[c] = 'REGISTRO_LINK'

        df_fmr.rename(columns=col_map_fmr, inplace=True)

        created_fmrs = 0
        for index, row in df_fmr.iterrows():
            fmr_code = clean_val(row.get("FMR_CODE"))
            if not fmr_code or fmr_code.lower() == 'nan':
                continue

            fecha = clean_date(row.get("FECHA"))
            cotizacion = clean_val(row.get("COTIZACION"))
            oc_num = clean_val(row.get("N_OC"))
            guia_despacho = clean_val(row.get("GUIA_DESPACHO"))
            factura = clean_val(row.get("FACTURA"))
            registro_link = clean_val(row.get("REGISTRO_LINK"))

            # Try to associate with OrdenCompra
            oc = None
            if oc_num and oc_num.lower() != 'nan':
                try:
                    oc = OrdenCompra.objects.get(numero_oc=oc_num)
                except OrdenCompra.DoesNotExist:
                    cleaned_oc_num = oc_num.strip()
                    try:
                        oc = OrdenCompra.objects.get(numero_oc__icontains=cleaned_oc_num)
                    except (OrdenCompra.DoesNotExist, OrdenCompra.MultipleObjectsReturned):
                        # Create a skeleton OC so they are linked
                        self.stdout.write(f"Warning: OC '{oc_num}' in FMR sheet not found in Control OC. Creating skeleton OC.")
                        oc = OrdenCompra.objects.create(
                            numero_oc=oc_num,
                            cliente="FLUOR SALFA LTDA",
                            descripcion=f"Creado automáticamente desde FMR {fmr_code}"
                        )

            # Create FMR
            try:
                FMR.objects.create(
                    fmr_code=fmr_code,
                    orden_compra=oc,
                    fecha=fecha,
                    cotizacion=cotizacion,
                    guia_despacho=guia_despacho,
                    factura=factura,
                    registro_link=registro_link if registro_link.startswith("http") else None
                )
                created_fmrs += 1
            except Exception as e:
                self.stderr.write(f"Error importing FMR {fmr_code}: {e}")

        # Recalculate all OC progress percentages based on the seeded delivery data
        self.stdout.write("Recalculating all OC percentages...")
        for oc in OrdenCompra.objects.all():
            oc.recalcular_porcentaje()

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {created_fmrs} FMR Records."))
        self.stdout.write(self.style.SUCCESS("Database seeding complete!"))
