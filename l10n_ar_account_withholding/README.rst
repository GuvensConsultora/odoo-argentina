.. |company| replace:: ADHOC SA

.. |company_logo| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-logo.png
   :alt: ADHOC SA
   :target: https://www.adhoc.com.ar

.. |icon| image:: https://raw.githubusercontent.com/ingadhoc/maintainer-tools/master/resources/adhoc-icon.png

.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

==============================================
Automatic Argentinian Withholdings on Payments
==============================================

Escala de Retenciones de Ganancias (Marzo 2026)
------------------------------------------------

+---+-------------------+-------------------+-------------------+-----+-------------------+
| # | Desde             | Hasta             | Fijo              |  %  | Excedente de      |
+===+===================+===================+===================+=====+===================+
| 1 |              0,00 |        500.007,52 |              0,00 |  5% |              0,00 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 2 |        500.007,52 |      1.000.015,04 |         25.000,38 |  9% |        500.007,52 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 3 |      1.000.015,04 |      1.500.022,56 |         70.001,05 | 12% |      1.000.015,04 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 4 |      1.500.022,56 |      2.250.033,85 |        130.001,96 | 15% |      1.500.022,56 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 5 |      2.250.033,85 |      4.500.067,70 |        242.503,65 | 19% |      2.250.033,85 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 6 |      4.500.067,70 |      6.750.101,55 |        670.010,08 | 23% |      4.500.067,70 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 7 |      6.750.101,55 |     10.125.152,32 |      1.187.517,87 | 27% |      6.750.101,55 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 8 |     10.125.152,32 |     15.187.728,49 |      2.098.781,57 | 31% |     10.125.152,32 |
+---+-------------------+-------------------+-------------------+-----+-------------------+
| 9 |     15.187.728,49 |               +∞  |      3.668.180,19 | 35% |     15.187.728,49 |
+---+-------------------+-------------------+-------------------+-----+-------------------+

Ejemplos de validación
----------------------

**Ejemplo 1 — Inscripto con % directo (Régimen 78, Venta de bienes)**

- Partner: imp_ganancias_padron = ``AC`` (Inscripto)
- Régimen 78: 2% inscripto, monto no sujeto $224.000
- Importe a pagar: $1.500.000

::

    Base imponible = $1.500.000 - $224.000 = $1.276.000
    Retención      = $1.276.000 × 2% = $25.520,00

**Ejemplo 2 — Inscripto con Escala (Régimen 116 II, Profesionales liberales)**

- Partner: imp_ganancias_padron = ``AC`` (Inscripto)
- Régimen 116 II: porcentaje_inscripto = -1 (escala), monto no sujeto $16.830
- Importe a pagar: $2.000.000

::

    Base imponible = $2.000.000 - $16.830 = $1.983.170
    Tramo 4: $1.500.022,56 — $2.250.033,85 (fijo $130.001,96 / 15%)
    Retención = $130.001,96 + ($1.983.170 - $1.500.022,56) × 15%
              = $130.001,96 + $483.147,44 × 0,15
              = $130.001,96 + $72.472,12
              = $202.474,08

**Ejemplo 3 — No Inscripto (Régimen 94, Locaciones de obra/servicios)**

- Partner: imp_ganancias_padron = ``NI`` (No Inscripto)
- Régimen 94: 28% no inscripto
- Importe a pagar: $500.000

::

    Retención = $500.000 × 28% = $140.000,00

Nota: para NI se aplica el porcentaje directamente sobre el total,
sin restar monto no sujeto a retención.

**Ejemplo 4 — Exento**

- Partner: imp_ganancias_padron = ``EX`` (Exento)
- Importe a pagar: $3.000.000

::

    Retención = $0,00 (no genera línea de retención)

Actualización de la escala
--------------------------

Para aplicar la escala en la base de datos, ejecutar::

    ./odoo-bin -u l10n_ar_account_withholding -d NOMBRE_BASE --stop-after-init

Los registros de ``afip.tabla_ganancias.escala`` se actualizan por XML ID (``escala_1`` a ``escala_9``).

TODO
----

- A script de instalación sumarle algo tipo esto, por ahora se puede correr manual.
  En realidad solo es necesario si estamos en localización o algo que requiera doble validación:
  ``UPDATE account_payment_group SET retencion_ganancias='no_aplica' WHERE retencion_ganancias is null;``
- El ajuste de cálculo de impuestos en pedidos de venta (por compatibilidad con ARBA) lo hicimos en
  sale_usability, habría que hacerlo en un módulo de la localización.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: http://runbot.adhoc.com.ar/

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ingadhoc/odoo-argentina/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* |company| |icon|

Contributors
------------

Maintainer
----------

|company_logo|

This module is maintained by the |company|.

To contribute to this module, please visit https://www.adhoc.com.ar.
