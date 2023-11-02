/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { TagsList } from "@web/views/fields/many2many_tags/tags_list";

const { Component, useState } = owl;

export class BankRecWidgetFormLinesWidget extends Component {
    setup() {
        this.state = useState({extraNoteVisible: false});

        this.bankRecService = useService("bank_rec_widget");
    }

    range(n) {
        return [...Array(Math.max(n, 0)).keys()];
    }

    get record() {
        return this.props.record;
    }

    /** Create the data to render the template **/
    getRenderValues() {
        let data = this.record.data.lines_widget;

        // Prepare columns.
        let columns = [
            ["account", this.env._t("Account")],
            ["partner", this.env._t("Partner")],
            ["date", this.env._t("Date")],
            ["label", this.env._t("Label")],
        ];
        if(data.display_analytic_account_column){
            columns.push(["analytic_account", this.env._t("Analytic Account")]);
        }
        if(data.display_multi_currency_column){
            columns.push(["amount_currency", this.env._t("Amount in Currency")], ["currency", this.env._t("Currency")]);
        }
        if(data.display_taxes_column){
            columns.push(["taxes", this.env._t("Taxes")]);
        }
        columns.push(["debit", this.env._t("Debit")], ["credit", this.env._t("Credit")], ["__trash", ""]);

        return {...data, columns: columns}
    }

    /** The user clicked on a row **/
    async mountLine(ev, lineIndex, clickedColumn=null) {
        if (!clickedColumn && ev.target.attributes && ev.target.attributes.field) {
            clickedColumn = ev.target.attributes['field'].value;
        }

        if(this.record.data.state == "reconciled"){
            // No edition allowed when the statement line is already reconciled.
            return;
        }

        const currentLineIndex = this.record.data.form_index;
        if(lineIndex != currentLineIndex){
            // Mount the line in edition on the form.
            await this.record.update({todo_command: `mount_line_in_edit,${lineIndex}`});

            this.bankRecService.trigger("form-notebook-activate-manual-op-page");
        }

        // Track the clicked column to focus automatically the corresponding field on the manual operations page.
        if(clickedColumn){
            this.bankRecService.trigger("form-clicked-column", clickedColumn);
        }
    }

    /** The user clicked on the trash button **/
    async removeLine(lineIndex) {
        if(this.record.data.state == "reconciled"){
            // No edition allowed when the statement line is already reconciled.
            return;
        }

        // Remove the line.
        await this.record.update({todo_command: `remove_line,${lineIndex}`});
        this.bankRecService.trigger("form-notebook-exit-manual-op-if-active");
    }

    /** The user clicked on the link to see the journal entry details **/
    async showMove(move_id) {
        await this.record.update({todo_command: `button_clicked,button_form_redirect_to_move_form,${move_id}`});
        this.bankRecService.trigger("kanban-do-action", this.record.data.next_action_todo);
    }

}
BankRecWidgetFormLinesWidget.template = "account_accountant.bank_rec_widget_form_lines_widget";
BankRecWidgetFormLinesWidget.props = {
    ...standardFieldProps,
}
BankRecWidgetFormLinesWidget.components = { TagsList };

registry.category("fields").add("bank_rec_widget_form_lines_widget", BankRecWidgetFormLinesWidget);
