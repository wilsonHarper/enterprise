from odoo import fields
from odoo.tests import tagged

from odoo.addons.account_reports.tests.common import TestAccountReportsCommon


@tagged("post_install", "post_install_l10n", "-at_install")
class TestPeSales(TestAccountReportsCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref="l10n_pe.pe_chart_template"):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company_data["company"].country_id = cls.env.ref("base.pe")
        cls.company_data["company"].vat = "20512528458"
        cls.partner_a.write({"country_id": cls.env.ref("base.pe").id, "vat": "20557912879"})
        cls.partner_b.write({"country_id": cls.env.ref("base.pe").id, "vat": "20557912879"})

        cls.sale_taxes = cls._get_sale_taxes()

    @classmethod
    def _get_sale_taxes(cls):
        taxes = cls.env["account.tax"]
        for tax in ["igv_18", "igv_18_included", "exo", "ina", "gra", "exp", "ics_0"]:
            taxes += cls.env.ref(f"l10n_pe.{cls.env.company.id}_sale_tax_{tax}")
        cls.env.ref(f"l10n_pe.{cls.env.company.id}_sale_tax_ics_0").amount = 10

        return taxes

    def test_sale_report(self):
        date_invoice = "2022-07-01"
        moves_vals = []
        for i, tax in enumerate(self.sale_taxes):
            for partner in (self.partner_a, self.partner_b):
                moves_vals += [
                    {
                        "move_type": "out_invoice",
                        "partner_id": partner.id,
                        "invoice_date": date_invoice,
                        "invoice_date_due": date_invoice,
                        "date": date_invoice,
                        "invoice_payment_term_id": False,
                        "l10n_latam_document_type_id": self.env.ref("l10n_pe.document_type01").id,
                        "invoice_line_ids": [
                            (0, 0, {
                                "name": f"test {tax.amount}",
                                "quantity": 1,
                                "price_unit": 10 + 1 * i,
                                "tax_ids": [(6, 0, tax.ids)],
                            })
                        ],
                    },
                    {
                        "move_type": "out_refund",
                        "partner_id": partner.id,
                        "invoice_date": date_invoice,
                        "invoice_date_due": date_invoice,
                        "date": date_invoice,
                        "invoice_payment_term_id": False,
                        "invoice_line_ids": [
                            (0, 0, {
                                "name": f"test {tax.amount}",
                                "quantity": 1,
                                "price_unit": 10 + 2 * i,
                                "tax_ids": [(6, 0, tax.ids)],
                            })
                        ],
                    },
                ]

        moves = self.env["account.move"].create(moves_vals)
        moves.action_post()
        moves.write({"edi_state": "sent"})

        # Move in draft must be ignored
        moves[0].copy()

        report = self.env.ref("l10n_pe_reports.tax_report_ple_sales_14_1")
        options = self._generate_options(
            report, fields.Date.from_string("2022-01-01"), fields.Date.from_string("2022-12-31")
        )

        self.maxDiff = None
        self.assertEqual(
            "\n".join(
                [
                    "|".join(line.split("|")[3:])
                    for line in self.env[report.custom_handler_model_name]
                    .export_to_txt(options)["file_content"]
                    .decode()
                    .split("\r\n")
                ]
            ),
            """
01/07/2022|01/07/2022|07|FCNE|00000001||0|20557912879|partner_a||-10.0||-1.8|||||||0.00||-11.8|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000002||0|20557912879|partner_b||-10.0||-1.8|||||||0.00||-11.8|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000003||0|20557912879|partner_a||-10.17||-1.83|||||||0.00||-12.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000004||0|20557912879|partner_b||-10.17||-1.83|||||||0.00||-12.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000005||0|20557912879|partner_a||||||-14.0|||||0.00||-14.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000006||0|20557912879|partner_b||||||-14.0|||||0.00||-14.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000007||0|20557912879|partner_a|||||||-16.0||||0.00||-16.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000008||0|20557912879|partner_b|||||||-16.0||||0.00||-16.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000009||0|20557912879|partner_a|||||||||||0.00||-18.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000010||0|20557912879|partner_b|||||||||||0.00||-18.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000011||0|20557912879|partner_a|-20.0||||||||||0.00||-20.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000012||0|20557912879|partner_b|-20.0||||||||||0.00||-20.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000013||0|20557912879|partner_a||||||||-2.2|||0.00||-24.2|PEN|1.000||||||||1|
01/07/2022|01/07/2022|07|FCNE|00000014||0|20557912879|partner_b||||||||-2.2|||0.00||-24.2|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000001||0|20557912879|partner_a||10.0||1.8|||||||0.00||11.8|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000002||0|20557912879|partner_b||10.0||1.8|||||||0.00||11.8|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000003||0|20557912879|partner_a||9.32||1.68|||||||0.00||11.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000004||0|20557912879|partner_b||9.32||1.68|||||||0.00||11.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000005||0|20557912879|partner_a||||||12.0|||||0.00||12.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000006||0|20557912879|partner_b||||||12.0|||||0.00||12.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000007||0|20557912879|partner_a|||||||13.0||||0.00||13.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000008||0|20557912879|partner_b|||||||13.0||||0.00||13.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000009||0|20557912879|partner_a|||||||||||0.00||14.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000010||0|20557912879|partner_b|||||||||||0.00||14.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000011||0|20557912879|partner_a|15.0||||||||||0.00||15.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000012||0|20557912879|partner_b|15.0||||||||||0.00||15.0|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000013||0|20557912879|partner_a||||||||1.6|||0.00||17.6|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000014||0|20557912879|partner_b||||||||1.6|||0.00||17.6|PEN|1.000||||||||1|
"""[
                1:
            ],
        )

    def test_sale_report_icbper(self):
        date_invoice = "2022-07-01"
        moves_vals = []

        taxes = self.env.ref(f"l10n_pe.{self.env.company.id}_sale_tax_igv_18")
        taxes |= taxes.create(
            {
                "name": "icbper",
                "amount_type": "fixed",
                "amount": 0.4,
                "l10n_pe_edi_tax_code": "7152",
                "l10n_pe_edi_unece_category": "S",
                "type_tax_use": "sale",
                "tax_group_id": self.env.ref("l10n_pe.tax_group_icbper").id,
                "include_base_amount": True,
            }
        )

        for partner in (self.partner_a, self.partner_b):
            moves_vals += [
                {
                    "move_type": "out_invoice",
                    "partner_id": partner.id,
                    "invoice_date": date_invoice,
                    "invoice_date_due": date_invoice,
                    "date": date_invoice,
                    "invoice_payment_term_id": False,
                    "l10n_latam_document_type_id": self.env.ref("l10n_pe.document_type01").id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "test",
                                "quantity": 1,
                                "price_unit": 100,
                                "tax_ids": [(6, 0, taxes.ids)],
                            },
                        )
                    ],
                },
            ]

        moves = self.env["account.move"].create(moves_vals)
        moves.action_post()
        moves.write({"edi_state": "sent"})

        report = self.env.ref("l10n_pe_reports.tax_report_ple_sales_14_1")
        options = self._generate_options(
            report, fields.Date.from_string("2022-01-01"), fields.Date.from_string("2022-12-31")
        )
        report._get_lines(options)

        self.maxDiff = None
        self.assertEqual(
            "\n".join(
                [
                    "|".join(line.split("|")[3:])
                    for line in self.env[report.custom_handler_model_name]
                    .export_to_txt(options)["file_content"]
                    .decode()
                    .split("\r\n")
                ]
            ),
            """
01/07/2022|01/07/2022|01|FFFI|00000001||0|20557912879|partner_a||100.0||18.0|||||||0.4||118.4|PEN|1.000||||||||1|
01/07/2022|01/07/2022|01|FFFI|00000002||0|20557912879|partner_b||100.0||18.0|||||||0.4||118.4|PEN|1.000||||||||1|
"""[
                1:
            ],
        )
