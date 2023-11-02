# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from freezegun import freeze_time

from odoo.addons.appointment.tests.test_appointment_ui import AppointmentUICommon
from odoo.addons.appointment_hr.tests.common import AppointmentHrCommon
from odoo.tests import tagged, users


@tagged('appointment_ui', '-at_install', 'post_install')
class AppointmentHrUITest(AppointmentUICommon, AppointmentHrCommon):

    @users('apt_manager')
    def test_route_apt_type_search_create_work_hours(self):
        self.authenticate(self.env.user.login, self.env.user.login)
        request = self.url_open(
            "/appointment/calendar_appointment_type/search_create_work_hours",
            data=json.dumps({}),
            headers={"Content-Type": "application/json"},
        ).json()
        result = request.get('result', dict())
        self.assertTrue(result.get('id'), 'The request returns the id of the custom appointment type')

        appointment_type = self.env['calendar.appointment.type'].browse(result['id'])
        self.assertEqual(appointment_type.category, 'work_hours')
        self.assertEqual(len(appointment_type.slot_ids), 14, "T14 slots have been created: 2 / day, 7 days")
        self.assertTrue(all(slot.slot_type == 'recurring' for slot in appointment_type.slot_ids), "All slots are 'recurring'")
        self.assertTrue(appointment_type.work_hours_activated)

    @users('apt_manager')
    def test_route_apt_type_search_create_work_hours_multicompany(self):
        """
        Test that slots that are based on work hours of the user are getting the employee it has,
        regardless of which company the employee belongs to.
        Use case would be in a multi-website multi-company context:
        An employee of Odoo SA would like to allow appointment based on workhours on the Odoo HK website.
        Before since the employee was defined in Odoo SA, the employee would not be found, and generic slots
        were returned. Now in case the employee is not in the company of the website, we search for the employee
        in all companies, and return the first one.
        """
        other_company = self.env['res.company'].sudo().create({
            'name': 'Other Company'
        })
        with freeze_time(self.reference_now):
            self.authenticate(self.env.user.login, self.env.user.login)
            request = self.url_open(
                "/appointment/calendar_appointment_type/search_create_work_hours",
                data=json.dumps({}),
                headers={"Content-Type": "application/json"},
            ).json()
            result = request.get('result', dict())
            self.assertTrue(result.get('id'), 'The request returns the id of the custom appointment type')
            appointment_type = self.env['calendar.appointment.type'].browse(result['id'])
            self.assertEqual(appointment_type.category, 'work_hours')
            self.assertTrue(appointment_type.work_hours_activated)
            # generate slots based on the company of the employee
            slots_employee_company = appointment_type.with_context(allowed_company_ids=[self.env.user.employee_id.company_id.id])._get_appointment_slots('Europe/Brussels', staff_user=self.env.user)
            # generate slots based on another company where the user doesn't have an employee defined
            slots_other_company = appointment_type.with_context(allowed_company_ids=[other_company.id])._get_appointment_slots('Europe/Brussels', staff_user=self.env.user)
            self.assertEqual(slots_employee_company, slots_other_company)
