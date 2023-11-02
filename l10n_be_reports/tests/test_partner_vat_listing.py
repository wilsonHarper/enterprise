# -*- coding: utf-8 -*-
# pylint: disable=C0326
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields
from odoo.tests import tagged
from odoo.addons.account_reports.tests.common import TestAccountReportsCommon

from freezegun import freeze_time


@tagged('post_install_l10n', 'post_install', '-at_install')
class BelgiumPartnerVatListingTest(TestAccountReportsCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref='l10n_be.l10nbe_chart_template'):
        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.partner_a_be = cls.env['res.partner'].create({
            'name': 'Partner A (BE)',
            'country_id': cls.env.ref('base.be').id,
            'vat': 'BE0246697724',
        })

        cls.partner_b_be = cls.env['res.partner'].create({
            'name': 'Partner B (BE)',
            'country_id': cls.env.ref('base.be').id,
            'vat': 'BE0766998497',
        })

        cls.report = cls.env.ref('l10n_be_reports.l10n_be_partner_vat_listing')

    @classmethod
    def setup_company_data(cls, company_name, chart_template=None, **kwargs):
        res = super().setup_company_data(company_name, chart_template=chart_template, **kwargs)
        res['company'].update({
            'country_id': cls.env.ref('base.be').id,
            'vat': 'BE0477472701',
        })
        res['company'].partner_id.update({
            'email': 'jsmith@mail.com',
            'phone': '+32475123456',
        })
        return res

    @classmethod
    def create_and_post_account_move(cls, move_type, partner_id, invoice_date, product_quantity, product_price_unit):
        move = cls.env['account.move'].create({
            'move_type': move_type,
            'partner_id': partner_id,
            'invoice_date': invoice_date,
            'date': fields.Date.from_string(invoice_date),
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product_a.id,
                'quantity': product_quantity,
                'name': 'Product 1',
                'price_unit': product_price_unit,
                'tax_ids': cls.tax_sale_a.ids,
            })]
        })

        move.action_post()
        return move

    def test_simple_invoice(self):
        self.env.companies = self.env.company
        options = self._generate_options(self.report, fields.Date.from_string('2022-06-01'), fields.Date.from_string('2022-06-30'))

        # Foreign partners invoices should not show
        self.create_and_post_account_move('out_invoice', self.partner_a.id, '2022-06-01', product_quantity=100, product_price_unit=50)

        # Belgian partners with out-of-date range invoices should not be shown
        self.create_and_post_account_move('out_invoice', self.partner_b_be.id, '2022-07-01', product_quantity=10, product_price_unit=200)

        # Invoices from Belgian partners should show up ordered by vat number
        self.create_and_post_account_move('out_invoice', self.partner_b_be.id, '2022-06-01', product_quantity=10, product_price_unit=200)
        self.create_and_post_account_move('out_invoice', self.partner_a_be.id, '2022-06-01', product_quantity=10, product_price_unit=100)

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                        VAT number          Turnover            VAT amount
            [   0,                          1,                  2,                  3],
            [
                ('Partner VAT Listing',     '',                 3000.0,             630.0),
                ('Partner A (BE)',          'BE0246697724',     1000.0,             210.0),
                ('Partner B (BE)',          'BE0766998497',     2000.0,             420.0),
            ],
        )

    def test_misc_operation(self):
        self.env.companies = self.env.company
        options = self._generate_options(self.report, fields.Date.from_string('2022-06-01'), fields.Date.from_string('2022-06-30'))

        move_1 = self.create_and_post_account_move('out_invoice', self.partner_b_be.id, '2022-06-01', product_quantity=10, product_price_unit=200)
        move_2 = self.create_and_post_account_move('out_invoice', self.partner_a_be.id, '2022-06-01', product_quantity=10, product_price_unit=100)

        # Those moves are misc operations that are identical to invoices
        (move_1 + move_2).write({'move_type': 'entry', 'date': '2022-06-01'})

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                        VAT number          Turnover            VAT amount
            [   0,                          1,                  2,                  3],
            [
                ('Partner VAT Listing',     '',                 3000.0,             630.0),
                ('Partner A (BE)',          'BE0246697724',     1000.0,             210.0),
                ('Partner B (BE)',          'BE0766998497',     2000.0,             420.0),
            ],
        )

    def test_invoices_with_refunds(self):
        self.env.companies = self.env.company
        options = self._generate_options(self.report, fields.Date.from_string('2022-06-01'), fields.Date.from_string('2022-06-30'))

        # Partial refund
        self.create_and_post_account_move('out_invoice', self.partner_a_be.id, '2022-06-01', product_quantity=10, product_price_unit=100)
        self.create_and_post_account_move('out_refund', self.partner_a_be.id, '2022-06-02', product_quantity=2, product_price_unit=100)

        # Full refund
        self.create_and_post_account_move('out_invoice', self.partner_b_be.id, '2022-06-01', product_quantity=10, product_price_unit=200)
        self.create_and_post_account_move('out_refund', self.partner_b_be.id, '2022-06-01', product_quantity=10, product_price_unit=200)

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                        VAT number          Turnover            VAT amount
            [   0,                          1,                  2,                  3],
            [
                ('Partner VAT Listing',     '',                 800.0,              168.0),
                ('Partner A (BE)',          'BE0246697724',     800.0,              168.0),
                ('Partner B (BE)',          'BE0766998497',     0.0,                0.0),
            ],
        )

    def test_refunds_without_invoices(self):
        self.env.companies = self.env.company
        options = self._generate_options(self.report, fields.Date.from_string('2022-06-01'), fields.Date.from_string('2022-06-30'))

        self.create_and_post_account_move('out_refund', self.partner_a_be.id, '2022-06-02', product_quantity=10, product_price_unit=100)

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                        VAT number          Turnover            VAT amount
            [   0,                          1,                  2,                  3],
            [
                ('Partner VAT Listing',     '',                 -1000.0,            -210.0),
                ('Partner A (BE)',          'BE0246697724',     -1000.0,            -210.0),
            ],
        )

    def test_zero_tax(self):
        self.env.companies = self.env.company
        options = self._generate_options(self.report, fields.Date.from_string('2022-06-01'), fields.Date.from_string('2022-06-30'))

        self.tax_sale_a.amount = 0
        self.init_invoice('out_invoice', partner=self.partner_a_be, post=True, amounts=[1000], taxes=[self.tax_sale_a], invoice_date='2022-06-29')

        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                        VAT number          Turnover            VAT amount
            [   0,                          1,                  2,                  3],
            [
                ('Partner VAT Listing',     '',                 1000.0,            0.0),
                ('Partner A (BE)',          'BE0246697724',     1000.0,            0.0),
            ],
        )

    @freeze_time('2019-12-31')
    def test_generate_xml_minimal(self):
        options = self.report._get_options(None)

        # The sequence changes between execution of the test. To handle that, we increase by 1 more, so we can get its value here
        sequence_number = self.env['ir.sequence'].next_by_code('declarantnum')
        ref = f"0477472701{str(int(sequence_number) + 1).zfill(4)[-4:]}"

        # This is the minimum expected from the belgian tax report xml.
        # As no values are in the report, we only find the grid 71 which is always expected to be present.
        expected_xml = """
            <ns2:ClientListingConsignment xmlns="http://www.minfin.fgov.be/InputCommon" xmlns:ns2="http://www.minfin.fgov.be/ClientListingConsignment" ClientListingsNbr="1">
                <ns2:ClientListing SequenceNumber="1" ClientsNbr="0" DeclarantReference="%s" TurnOverSum="0.00" VATAmountSum="0.00">
                    <ns2:Declarant>
                        <VATNumber>0477472701</VATNumber>
                        <Name>company_1_data</Name>
                        <Street></Street>
                        <PostCode></PostCode>
                        <City></City>
                        <CountryCode>BE</CountryCode>
                        <EmailAddress>jsmith@mail.com</EmailAddress>
                        <Phone>+32475123456</Phone>
                    </ns2:Declarant>
                    <ns2:Period>2018</ns2:Period>
                    <ns2:Comment></ns2:Comment>
                </ns2:ClientListing>
            </ns2:ClientListingConsignment>
        """ % ref

        self.assertXmlTreeEqual(
            self.get_xml_tree_from_string(self.env[self.report._get_custom_handler_model()].partner_vat_listing_export_to_xml(options)['file_content']),
            self.get_xml_tree_from_string(expected_xml)
        )

    def test_no_vat(self):
        """
        Test whether when there is partner's vat starting with "be", the report does not crash
        """
        self.env['res.partner'].search([]).write({'vat': False})
        options = self.report._get_options(None)
        self.assertLinesValues(
            self.report._get_lines(options),
            #   Name                        VAT number          Turnover            VAT amount
            [   0,                          1,                  2,                  3],
            [
                ('Partner VAT Listing',     '',                 0,                  0),
            ],
        )

    @freeze_time('2019-12-31')
    def test_generate_xml_minimal_with_representative(self):
        company = self.env.company
        options = self.report._get_options(None)

        # Create a new partner for the representative and link it to the company.
        representative = self.env['res.partner'].create({
            'company_type': 'company',
            'name': 'Fidu BE',
            'street': 'Fidu Street 123',
            'city': 'Brussels',
            'zip': '1000',
            'country_id': self.env.ref('base.be').id,
            'vat': 'BE0477472701',
            'mobile': '+32470123456',
            'email': 'info@fidu.be',
        })
        company.account_representative_id = representative.id

        # The sequence changes between execution of the test. To handle that, we increase by 1 more, so we can get its value here
        sequence_number = self.env['ir.sequence'].next_by_code('declarantnum')
        ref = f"0477472701{str(int(sequence_number) + 1).zfill(4)[-4:]}"

        # This is the minimum expected from the belgian tax report XML.
        # Only the representative node has been added to make sure it appears in the XML.
        expected_xml = """
            <ns2:ClientListingConsignment xmlns="http://www.minfin.fgov.be/InputCommon" xmlns:ns2="http://www.minfin.fgov.be/ClientListingConsignment" ClientListingsNbr="1">
                <ns2:Representative>
                    <RepresentativeID identificationType="NVAT" issuedBy="BE">0477472701</RepresentativeID>
                    <Name>Fidu BE</Name>
                    <Street>Fidu Street 123</Street>
                    <PostCode>1000</PostCode>
                    <City>Brussels</City>
                    <CountryCode>BE</CountryCode>
                    <EmailAddress>info@fidu.be</EmailAddress>
                    <Phone>+32470123456</Phone>
                </ns2:Representative>
                <ns2:ClientListing SequenceNumber="1" ClientsNbr="0" DeclarantReference="%s" TurnOverSum="0.00" VATAmountSum="0.00">
                    <ns2:Declarant>
                        <VATNumber>0477472701</VATNumber>
                        <Name>company_1_data</Name>
                        <Street></Street>
                        <PostCode></PostCode>
                        <City></City>
                        <CountryCode>BE</CountryCode>
                        <EmailAddress>jsmith@mail.com</EmailAddress>
                        <Phone>+32475123456</Phone>
                    </ns2:Declarant>
                    <ns2:Period>2018</ns2:Period>
                    <ns2:Comment></ns2:Comment>
                </ns2:ClientListing>
            </ns2:ClientListingConsignment>
        """ % ref

        self.assertXmlTreeEqual(
            self.get_xml_tree_from_string(self.env[self.report._get_custom_handler_model()].partner_vat_listing_export_to_xml(options)['file_content']),
            self.get_xml_tree_from_string(expected_xml)
        )
