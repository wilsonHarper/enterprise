odoo.define('test_mrp_barcode_flows.tour', function(require) {
'use strict';

var tour = require('web_tour.tour');

tour.register('test_immediate_receipt_kit_from_scratch_with_tracked_compo', {test: true}, [
    {
        trigger: '.o_barcode_client_action',
        run: 'scan kit_lot',
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_edit',
    },
    {
        trigger: '.o_digipad_button.o_increase',
    },
    {
        trigger: '.o_save',
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_add_quantity'
    },
    {
        extra_trigger: '.o_barcode_line:contains("Kit Lot") .qty-done:contains("3")',
        trigger: '.btn.o_validate_page',
    },
    {
        trigger: '.o_notification.border-danger',
    },
    {
        extra_trigger: '.o_barcode_line:contains("Compo 01")',
        trigger: '.o_barcode_line:contains("Compo Lot")',
    },
    {
        trigger: '.o_selected:contains("Compo Lot")',
        run: 'scan super_lot',
    },
    {
        extra_trigger: '.o_line_lot_name:contains("super_lot")',
        trigger: '.btn.o_validate_page',
    },
    {
        trigger: '.o_notification.border-success',
    },
]);

tour.register('test_planned_receipt_kit_from_scratch_with_tracked_compo', {test: true}, [
    {
        trigger: '.o_barcode_client_action',
        run: 'scan kit_lot',
    },
    tour.stepUtils.confirmAddingUnreservedProduct(),
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_edit',
    },
    {
        trigger: '.o_digipad_button.o_increase',
    },
    {
        trigger: '.o_save',
    },
    {
        trigger: '.o_barcode_line:contains("Kit Lot") .o_add_quantity'
    },
    {
        extra_trigger: '.o_barcode_line:contains("Kit Lot") .qty-done:contains("3")',
        trigger: '.btn.o_validate_page',
    },
    {
        trigger: '.o_notification.border-danger',
    },
    {
        extra_trigger: '.o_barcode_line:contains("Compo 01")',
        trigger: '.o_barcode_line:contains("Compo Lot")',
    },
    {
        trigger: '.o_selected:contains("Compo Lot")',
        run: 'scan super_lot',
    },
    {
        extra_trigger: '.o_line_lot_name:contains("super_lot")',
        trigger: '.btn.o_validate_page',
    },
    {
        trigger: '.o_notification.border-success',
    },
]);

});
