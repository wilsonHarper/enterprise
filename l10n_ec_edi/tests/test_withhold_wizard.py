# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from freezegun import freeze_time
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestEcEdiCommon


@tagged('post_install_l10n', 'post_install', '-at_install')
class TestEcEdiWithholdWizard(TestEcEdiCommon):

    # ===== TEST METHODS =====

    def test_out_withhold_basic_computes(self):
        wizard, out_invoice = self.get_wizard_and_invoice()
        self.assertFalse(wizard.withhold_line_ids)  # out_withhold has no default withhold lines

        self.env['l10n_ec.wizard.account.withhold.line'].create({
            'invoice_id': out_invoice.id,
            'wizard_id': wizard.id,
            'tax_id': self._get_tax_by_xml_id('tax_sale_withhold_vat_10').ids[0],
        })
        # creating a withhold line yields the expected values
        self.assertEqual(len(wizard.withhold_line_ids), 1)
        withhold_line = wizard.withhold_line_ids[0]
        self.assertEqual(withhold_line.taxsupport_code, False)
        self.assertEqual(withhold_line.base, 48)
        self.assertEqual(withhold_line.amount, 4.8)

    def test_out_withhold_basic_checks(self):
        wizard, out_invoice = self.get_wizard_and_invoice()

        with self.assertRaises(ValidationError):
            wizard.action_create_and_post_withhold()  # empty withhold can't be posted

        with self.assertRaises(ValidationError):
            self.env['l10n_ec.wizard.account.withhold.line'].create({
                'invoice_id': out_invoice.id,
                'wizard_id': wizard.id,
                'tax_id': self._get_tax_by_xml_id('tax_sale_withhold_vat_10').ids[0],
                'amount': -10,  # no negative amount in withhold lines
            })

    def test_purchase_invoice_withhold(self, custom_taxpayer=False):
        """Creates a purchase invoice and checks that when adding a withhold
        - the suggested taxes match the product default taxes
        - the tax supports are a subset of the invoice's tax supports
        - the withhold is successfully posted"""

        # Create purchase invoice and withhold wizard
        wizard, purchase_invoice = self.get_wizard_and_purchase_invoice()

        # Validate if the withholding tax established in the product is in the field default line creation wizard
        if not custom_taxpayer:
            wizard_tax_ids = wizard.withhold_line_ids.mapped('tax_id')
            product_invoice_tax_ids = purchase_invoice.invoice_line_ids.mapped('product_id.l10n_ec_withhold_tax_id')
            self.assertTrue(all(p_tax.id in wizard_tax_ids.ids for p_tax in product_invoice_tax_ids))

        # Validation: wizard's tax supports is subset of invoice's tax supports
        wizard_tax_support = set(wizard.withhold_line_ids.mapped('taxsupport_code'))
        invoice_tax_support = set(purchase_invoice._l10n_ec_get_inv_taxsupports_and_amounts().keys())
        self.assertTrue(wizard_tax_support.issubset(invoice_tax_support))

        with freeze_time(self.frozen_today):
            withhold = wizard.action_create_and_post_withhold()
        self.assertEqual(withhold.state, 'posted')

    def test_custom_taxpayer_type_partner_on_purchase_invoice(self):
        """Tests test_purchase_invoice_withhold with a custom taxpayer as a partner."""
        self.set_custom_taxpayer_type_on_partner_a()
        self.test_purchase_invoice_withhold(custom_taxpayer=True)

    # ===== HELPER METHODS =====

    def get_wizard_and_invoice(self, invoice_args=None):
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
        }
        if invoice_args:
            invoice_vals.update(invoice_args)
        invoice = self.get_invoice(invoice_vals)
        invoice.action_post()
        wizard = self.env['l10n_ec.wizard.account.withhold'].with_context(active_ids=invoice.id, active_model='account.move')
        return wizard.create({}), invoice
