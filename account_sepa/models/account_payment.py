# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model
    def _get_method_codes_using_bank_account(self):
        res = super(AccountPayment, self)._get_method_codes_using_bank_account()
        res += ['sepa_ct']
        return res

    @api.model
    def _get_method_codes_needing_bank_account(self):
        res = super(AccountPayment, self)._get_method_codes_needing_bank_account()
        res += ['sepa_ct']
        return res

    @api.constrains('payment_method_line_id', 'journal_id')
    def _check_sepa_bank_account(self):
        sepa_payment_method = self.env.ref('account_sepa.account_payment_method_sepa_ct')
        for rec in self:
            if rec.payment_method_id == sepa_payment_method:
                if not rec.journal_id.bank_account_id or not rec.journal_id.bank_account_id.acc_type == 'iban':
                    raise ValidationError(_("The journal '%s' requires a proper IBAN account to pay via SEPA. Please configure it first.", rec.journal_id.name))

    def _get_payment_method_codes_to_exclude(self):
        res = super()._get_payment_method_codes_to_exclude()
        currency_codes = ['BGN', 'HRK', 'CZK', 'DKK', 'GIP', 'HUF', 'ISK', 'CHF', 'NOK', 'PLN', 'RON', 'SEK', 'GBP', 'EUR', 'XPF']
        currency_ids = self.env['res.currency'].with_context(active_test=False).search([('name', 'in', currency_codes)])
        sepa_ct = self.env.ref('account_sepa.account_payment_method_sepa_ct', raise_if_not_found=False)
        if sepa_ct and self.currency_id not in currency_ids:
            res.append(sepa_ct.code)
        return res
