# Argentina - Retenciones Automáticas en Pagos (Ganancias RG 830)

## 1. Introducción

### Qué hace Odoo nativamente
Odoo estándar con localización argentina (`l10n_ar`) gestiona el plan de cuentas AFIP, tipos de documentos y posiciones fiscales, pero **no calcula retenciones de Impuesto a las Ganancias** automáticamente en los pagos a proveedores.

### Limitación
Sin este módulo, el usuario debe calcular manualmente cada retención según la RG 830/AFIP, buscar la escala correspondiente, acumular pagos del período, restar montos no sujetos y generar el pago con el importe correcto. Esto es propenso a errores y consume tiempo.

### Qué resuelve este módulo
Automatiza el cálculo completo de retenciones de Ganancias (RG 830) al confirmar un pago a proveedor:

- **26 regímenes** de retención precargados (Anexo II de RG 830)
- **Régimen 119** para honorarios profesionales (RG 5423/2023) con escala propia
- **Escalas por régimen**: cada régimen puede tener su propia escala de tramos, o usar la escala general RG 830
- **Acumulación mensual**: acumula pagos del mismo mes/partner/régimen y descuenta retenciones previas
- **Soporte inscripto (AC)**, no inscripto (NI), exento (EX) y no corresponde (NC)
- **Percepciones IIBB**: alícuota por partner (ARBA/AGIP)

---

## 2. Funcionamiento para el usuario final

### Flujo de un pago con retención de Ganancias

1. **Crear orden de pago** (Contabilidad > Proveedores > Ordenes de pago)
2. **Seleccionar proveedor** — el sistema lee su inscripción en Ganancias (`AC`, `NI`, `EX`, `NC`)
3. **Elegir régimen** — se propone el default del partner, pero puede cambiarse
4. **Seleccionar facturas** a pagar (o indicar monto de adelanto)
5. **Confirmar** — el sistema calcula automáticamente:

### Ejemplo: Proveedor inscripto, régimen 119 (honorarios profesionales)

| Concepto | Valor |
|----------|-------|
| Factura neta | $400,000 |
| Monto no sujeto (régimen 119) | -$160,000 |
| Base imponible | $240,000 |
| Escala RG 5423 tramo 4: $18,460 + 15% x ($240,000 - $213,000) | **$22,510** |
| **Retención Ganancias** | **$22,510** |

### Ejemplo: Proveedor inscripto, régimen 78 (bienes de cambio, porcentaje fijo)

| Concepto | Valor |
|----------|-------|
| Factura neta | $500,000 |
| Monto no sujeto (régimen 78) | -$224,000 |
| Base imponible | $276,000 |
| 2% de $276,000 | **$5,520** |
| **Retención Ganancias** | **$5,520** |

### Ejemplo: Acumulación mensual (2 pagos en el mes)

| Pago | Base | No sujeto | Base imponible | Retención | Descuento previas | Neto a retener |
|------|------|-----------|----------------|-----------|-------------------|----------------|
| 1er pago | $100,000 | -$67,170 | $32,830 | $656.60 | $0 | **$656.60** |
| 2do pago | $80,000 + $100,000 acum. | -$67,170 | $112,830 | $2,256.60 | -$656.60 | **$1,600.00** |

### Regla: el monto no sujeto se descuenta una sola vez por mes
- Si ya hubo retención en el mes, no se vuelve a descontar
- El sistema acumula automáticamente todos los pagos del mes al mismo proveedor y régimen

### Qué ve el usuario
- En la orden de pago: línea automática de retención con el monto calculado
- En el campo "Comunicación": código de régimen + concepto (ej: "119 - Profesiones liberales...")
- Si el proveedor es exento (`EX`) o no corresponde (`NC`): no se genera retención

---

## 3. Parametrización

### Paso 1: Configurar el impuesto de retención

**Menú:** Contabilidad > Configuración > Impuestos

1. Crear un impuesto con:
   - **Tipo de retención:** `Tabla Ganancias`
   - **Monto base:** `Monto neto` (para usar la base sin IVA)
   - **Pagos acumulados:** `Mes` (acumula pagos mensuales)
   - **Mínimo no imponible:** monto mínimo para que se genere la retención

### Paso 2: Configurar el proveedor

**Menú:** Contabilidad > Proveedores > Proveedores

En la pestaña de datos fiscales:
1. **Inscripción Ganancias:** elegir `AC` (inscripto), `NI` (no inscripto), `EX` (exento) o `NC` (no corresponde)
2. **Régimen Ganancias por defecto:** elegir el régimen que aplica habitualmente (ej: 119 para profesionales, 78 para bienes, 94 para servicios)

### Paso 3: Verificar regímenes y escalas

**Menú:** Contabilidad > Configuración > AFIP > Alicuotas y Montos Ganancias

Verificar que existen los 26 regímenes. Para los que usan escala (`% Inscripto = -1`), al abrir el formulario se ve la pestaña "Escalas":
- Si tiene escalas propias (ej: régimen 119): se listan los 8 tramos RG 5423
- Si no tiene escalas propias (ej: régimen 116 II): usa la escala general RG 830

**Menú:** Contabilidad > Configuración > AFIP > Escalas Ganancias

Verificar las 16 escalas:
- 8 escalas generales RG 830 (columna "Régimen" vacía)
- 8 escalas RG 5423 (columna "Régimen" = 119)

### Paso 4: Configurar diario de retenciones

Asegurarse de que exista un diario de tipo "Efectivo" con el método de pago `Retenciones` habilitado en los métodos de pago salientes.

---

## 4. Referencia técnica

### Arquitectura

```
l10n_ar_account_withholding/
├── __manifest__.py
├── models/
│   ├── afip.py                  # Modelos de escalas y regímenes
│   └── account_tax.py           # Cálculo de retenciones (hereda account.tax)
├── data/
│   └── tabla_ganancias_data.xml # 26 regímenes + 16 escalas precargadas
├── views/
│   ├── afip_tabla_ganancias_escala_view.xml
│   ├── afip_tabla_ganancias_alicuotasymontos_view.xml
│   ├── account_payment_group_view.xml
│   ├── account_payment_view.xml
│   ├── res_company_view.xml
│   ├── res_partner_view.xml
│   └── afip_activity_view.xml
└── security/
    ├── ir.model.access.csv
    └── security.xml
```

### Modelos

#### `afip.tabla_ganancias.alicuotasymontos` — Regímenes de retención

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `codigo_de_regimen` | Char(6) | Código AFIP (ej: "119", "78", "116 II") |
| `anexo_referencia` | Char | Referencia al Anexo II de RG 830 |
| `concepto_referencia` | Text | Descripción del concepto gravado |
| `porcentaje_inscripto` | Float | % para inscriptos. **-1 = calcular por escala** |
| `porcentaje_no_inscripto` | Float | % para no inscriptos (flat) |
| `montos_no_sujetos_a_retencion` | Float | Monto no sujeto a retención |
| `escala_ids` | One2many → escala | Escalas específicas de este régimen |

#### `afip.tabla_ganancias.escala` — Tramos de escala

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `regimen_id` | Many2one → alicuotasymontos | Régimen al que pertenece. **False = escala general** |
| `importe_desde` | Float | Límite inferior del tramo |
| `importe_hasta` | Float | Límite superior del tramo |
| `importe_fijo` | Float | Monto fijo del tramo |
| `porcentaje` | Float | Porcentaje sobre excedente |
| `importe_excedente` | Float | Base del excedente |

**Lógica de selección de escala:**
- Si `regimen.escala_ids` tiene registros → buscar con `regimen_id = regimen.id`
- Si no → buscar con `regimen_id = False` (escala general RG 830)

### Métodos de cálculo (`account.tax`)

#### `get_withholding_vals(payment_group)`
Método principal. Determina el tipo de partner (AC, NI, EX, NC) y delega:
- `AC` → `_compute_ganancias_inscripto()`
- `NI` → porcentaje fijo directo (`porcentaje_no_inscripto`)
- `EX`/`NC` → retención = 0

#### `_compute_ganancias_inscripto(payment_group, regimen, vals)`
Flujo completo para inscriptos:
1. Obtener base imponible → `_get_ganancias_base_amount()`
2. Acumular pagos del período → `_get_ganancias_accumulated()`
3. Restar monto no sujeto (1 sola vez por mes)
4. Calcular por escala o porcentaje fijo → `_compute_ganancias_escala()`
5. Verificar mínimo no imponible
6. Descontar retenciones previas del mes

```python
# Fórmula de la escala:
retencion = escala.importe_fijo + (escala.porcentaje / 100) * (base - escala.importe_excedente)
```

#### `_get_ganancias_base_amount(payment_group, vals)`
- Con facturas: suma el neto de cada factura usando `_get_tax_factor()` (ratio neto/total)
- Sin facturas (adelanto): usa `to_pay_amount`

#### `_get_ganancias_accumulated(payment_group)`
Una sola búsqueda de pagos previos del mes, mismo partner y régimen. Retorna:
- `accumulated_amount`: base de pagos previos sin retención de este impuesto
- `previous_withholding`: monto de retenciones previas (para descontar)
- `has_prev_withholding`: flag que indica si ya hubo retención (para no descontar monto no sujeto 2 veces)

#### `_compute_ganancias_escala(regimen, base_amount)`
Selecciona escala (específica o general) y aplica la fórmula de tramos.

### Datos precargados

**26 regímenes** — Anexo II de RG 830 + Factura M (99) + RG 5423 (119)

| Código | Concepto | % Inscr. | % No Inscr. | No sujeto |
|--------|----------|----------|-------------|-----------|
| 19 | Intereses entidades financieras | 3% | 10% | $0 |
| 21 | Intereses otros | 6% | 28% | $7,870 |
| 25 | Comisionistas (escala) | escala | 28% | $16,830 |
| 30-32 | Alquileres | 6% | 28% | $11,200 |
| 35 | Regalías | 6% | 28% | $7,870 |
| 78 | Bienes muebles/de cambio | 2% | 10% | $224,000 |
| 94 | Servicios varios | 2% | 28% | $67,170 |
| 110 | Derechos de autor (escala) | escala | 28% | $10,000 |
| 116 I | Directores SA (escala) | escala | 28% | $67,170 |
| 116 II | Directores/síndicos SRL (escala) | escala | 28% | $67,170 |
| **119** | **Profesionales liberales (escala RG 5423)** | **escala** | **28%** | **$160,000** |
| 124 | Corredores/despachantes (escala) | escala | 28% | $16,830 |
| 99 | Factura M | 3% | 3% | $1,000 |

**16 escalas** — 2 tablas de tramos:

**Escala general RG 830** (regímenes 25, 110, 116 I, 116 II, 124):

| Desde | Hasta | Fijo | % | Excedente |
|-------|-------|------|---|-----------|
| 0 | 5,000 | 0 | 5% | 0 |
| 5,000 | 10,000 | 250 | 9% | 5,000 |
| 10,000 | 15,000 | 700 | 12% | 10,000 |
| 15,000 | 20,000 | 1,300 | 15% | 15,000 |
| 20,000 | 30,000 | 2,050 | 19% | 20,000 |
| 30,000 | 40,000 | 3,950 | 23% | 30,000 |
| 40,000 | 60,000 | 6,250 | 27% | 40,000 |
| 60,000 | +inf | 11,650 | 31% | 60,000 |

**Escala RG 5423/2023** (solo régimen 119 — honorarios profesionales):

| Desde | Hasta | Fijo | % | Excedente |
|-------|-------|------|---|-----------|
| 0 | 71,000 | 0 | 5% | 0 |
| 71,000 | 142,000 | 3,550 | 9% | 71,000 |
| 142,000 | 213,000 | 9,940 | 12% | 142,000 |
| 213,000 | 284,000 | 18,460 | 15% | 213,000 |
| 284,000 | 426,000 | 29,110 | 19% | 284,000 |
| 426,000 | 568,000 | 56,090 | 23% | 426,000 |
| 568,000 | 852,000 | 88,750 | 27% | 568,000 |
| 852,000 | +inf | 165,430 | 31% | 852,000 |

### Bugs corregidos en v2.0.0

| Bug | Causa | Fix |
|-----|-------|-----|
| Journal siempre tomaba el primero | `payment_method.id == payment_method.id` (siempre True) | Comparar `outbound_payment_method.payment_method_id.id == payment_method.id` |
| Usaba régimen del partner en vez del pago | `partner.default_regimen_ganancias_id` en vez de `payment_group.regimen_ganancias_id` | Usar siempre el régimen del payment_group |
| Doble búsqueda de pagos previos | 2 searches redundantes con lógica inconsistente | Una sola búsqueda en `_get_ganancias_accumulated()` |
| Escala única global | No soportaba escalas diferentes por régimen | Campo `regimen_id` en escala + fallback a escala general |
| Código spaghetti con doble cálculo | 150+ líneas con lógica duplicada y variables sobreescritas | 4 métodos limpios con responsabilidad única |
| previous_withholding con tax_factor incorrecto | Iteraba `payment_group.debt_move_line_ids` del pago actual para factor del pago previo | Simplificado: el módulo base pasa `previous_withholding = 0`, el cálculo completo lo hace `l10n_ar` |

### Seguridad

| Modelo | Grupo | Lectura | Escritura | Crear | Eliminar |
|--------|-------|---------|-----------|-------|----------|
| `afip.tabla_ganancias.escala` | `account.group_account_manager` | Si | Si | Si | Si |
| `afip.tabla_ganancias.escala` | Todos | Si | No | No | No |
| `afip.tabla_ganancias.alicuotasymontos` | `account.group_account_manager` | Si | Si | Si | Si |
| `afip.tabla_ganancias.alicuotasymontos` | Todos | Si | No | No | No |

### Dependencias

- `account_withholding_automatic` — framework base de retenciones automáticas
- `l10n_ar` — localización argentina (AFIP, tipos de responsabilidad)
- `pyafipws` — librería Python para servicios web AFIP

### Verificación post-upgrade

```
-u l10n_ar_account_withholding
```

1. **Datos:** 26 regímenes en Alicuotas y Montos + 16 escalas (8 general + 8 reg.119)
2. **UI:** Menú Escalas Ganancias muestra columna "Régimen", agrupable
3. **UI:** Formulario de régimen con escala muestra pestaña "Escalas"
4. **Régimen 119 + escala propia:** Pago a profesional inscripto, base $300,000 → escala RG 5423
5. **Régimen 116 II + escala general:** Pago a director inscripto, base $50,000 → escala RG 830
6. **Régimen 78 (% fijo):** Pago bienes, base $500,000 → 2%
7. **No inscripto:** Partner NI → % flat directo
8. **Acumulación:** 2 pagos mismo mes → segundo acumula y resta retención previa
9. **Journal:** Retención se asigna al diario correcto (con método de pago Retenciones)

### Versión

`17.0.2.0.0`
