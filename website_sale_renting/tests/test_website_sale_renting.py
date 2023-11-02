# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from dateutil.relativedelta import relativedelta, FR, SA, SU

from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged
from .common import TestWebsiteSaleRentingCommon

@tagged('post_install', '-at_install')
class TestWebsiteSaleRenting(TestWebsiteSaleRentingCommon):

    @freeze_time('2023, 1, 1')
    def test_invalid_dates(self):
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
        })
        now = fields.Datetime.now()
        sol = self.env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': self.computer.id,
            'start_date': now + relativedelta(weekday=SA),
            'return_date': now + relativedelta(weeks=1, weekday=SU),
            'is_rental': True,
        })
        self.assertTrue(sol._is_invalid_renting_dates(sol.company_id), "Pickup and Return dates cannot be the same as renting unavailabilities days")
        sol.write({
            'start_date': now + relativedelta(weekday=FR),
            'return_date': now + relativedelta(weeks=1, weekday=SU),
        })
        self.assertTrue(sol._is_invalid_renting_dates(sol.company_id), "Return date cannot be the same as renting unavailabilities days")
        sol.write({
            'start_date': now + relativedelta(weekday=SU),
            'return_date': now + relativedelta(weeks=1, weekday=SA),
        })
        self.assertTrue(sol._is_invalid_renting_dates(sol.company_id), "Return date cannot be the same as renting unavailabilities days")
        sol.write({
            'start_date': now + relativedelta(weeks=1, weekday=SU),
            'return_date': now,
        })
        self.assertTrue(sol._is_invalid_renting_dates(sol.company_id), "Return date cannot be prior pickupdate")

    def test_add_rental_product_to_cart(self):
        """
        Make sure that we can add a rental product
        (only marked as "can be rented" and not "can be sold") to the shopping cart
        """
        self.computer.write({
            'website_published': True,
            'active': True,
            'sale_ok': False,
            'rent_ok': True,
        })
        self.assertTrue(self.computer._is_add_to_cart_allowed(), "Rental product should be addable to the cart")
