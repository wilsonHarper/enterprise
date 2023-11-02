/** @odoo-module */

import { makeView, setupViewRegistries } from "@web/../tests/views/helpers";
import {
    getFixture,
    editInput,
    patchWithCleanup,
    click,
    nextTick,
    makeDeferred,
} from "@web/../tests/helpers/utils";
import { createWebClient, doAction } from "@web/../tests/webclient/helpers";
import { session } from "@web/session";
import { registry } from "@web/core/registry";

const fakeStudioService = {
    start() {
        return {
            mode: null,
        };
    },
};

QUnit.module("Studio Approval", (hooks) => {
    let target;
    let serverData;

    hooks.beforeEach(() => {
        target = getFixture();

        serverData = {
            models: {
                partner: {
                    fields: {
                        display_name: { string: "Displayed name", type: "char" },
                        int_field: { string: "int_field", type: "integer", sortable: true },
                        bar: { string: "Bar", type: "boolean" },
                    },
                    records: [
                        {
                            id: 1,
                            display_name: "first record",
                            int_field: 42,
                            bar: true,
                        },
                        {
                            id: 2,
                            display_name: "second record",
                            int_field: 27,
                            bar: true,
                        },
                        {
                            id: 3,
                            display_name: "another record",
                            int_field: 21,
                            bar: false,
                        },
                    ],
                },
            },
        };

        setupViewRegistries();
        registry.category("services").add("studio", fakeStudioService);
    });

    QUnit.test("approval components are synchronous", async (assert) => {
        const prom = makeDeferred();
        await makeView({
            type: "form",
            resModel: "partner",
            serverData,
            arch: `<form><button studio_approval="True" type="object" name="myMethod"/></form>`,
            async mockRPC(route, args) {
                if (args.method === "get_approval_spec") {
                    assert.step(args.method);
                    await prom;
                    return {
                        rules: [
                            {
                                id: 1,
                                group_id: [1, "Internal User"],
                                domain: false,
                                can_validate: true,
                                message: false,
                                exclusive_user: false,
                            },
                        ],
                        entries: [],
                        groups: [[1, "Internal User"]],
                    };
                }
            },
        });
        assert.verifySteps(["get_approval_spec"]);
        assert.containsOnce(target, "button .o_web_studio_approval .fa-circle-o-notch.fa-spin");
        prom.resolve();
        await nextTick();
        assert.containsNone(target, "button .o_web_studio_approval .fa-circle-o-notch.fa-spin");
        assert.containsOnce(target, "button .o_web_studio_approval .o_web_studio_approval_avatar");
    });

    QUnit.test("approval widget basic rendering", async function (assert) {
        assert.expect(14);

        patchWithCleanup(session, {
            uid: 42,
        });

        await makeView({
            type: "form",
            resModel: "partner",
            serverData,
            arch: `<form string="Partners">
                <sheet>
                    <header>
                        <button type="object" name="someMethod" string="Apply Method" studio_approval="True"/>
                    </header>
                    <div name="button_box">
                        <button class="oe_stat_button" studio_approval="True" id="visibleStat">
                            <field name="int_field"/>
                        </button>
                        <button class="oe_stat_button" studio_approval="True"
                                attrs='{"invisible": [["bar", "=", true]]}' id="invisibleStat">
                            <field name="bar"/>
                        </button>
                    </div>
                    <group>
                        <group style="background-color: red">
                            <field name="display_name" studio_approval="True"/>
                            <field name="bar"/>
                            <field name="int_field"/>
                        </group>
                    </group>
                    <button type="object" name="anotherMethod"
                            string="Apply Second Method" studio_approval="True"/>
                </sheet>
            </form>`,
            resId: 2,
            mockRPC: function (route, args) {
                if (args.method === "get_approval_spec") {
                    assert.step("fetch_approval_spec");
                    return Promise.resolve({
                        rules: [
                            {
                                id: 1,
                                group_id: [1, "Internal User"],
                                domain: false,
                                can_validate: true,
                                message: false,
                                exclusive_user: false,
                            },
                        ],
                        entries: [],
                        groups: [[1, "Internal User"]],
                    });
                }
            },
        });

        // check that the widget was inserted on visible buttons only
        assert.containsOnce(target, 'button[name="someMethod"] .o_web_studio_approval');
        assert.containsOnce(target, "#visibleStat .o_web_studio_approval");
        assert.containsNone(target, "#invisibleStat .o_web_studio_approval");
        assert.containsOnce(target, 'button[name="anotherMethod"] .o_web_studio_approval');
        assert.containsNone(target, ".o_group .o_web_studio_approval");
        // should have fetched spec for exactly 3 buttons
        assert.verifySteps(["fetch_approval_spec", "fetch_approval_spec", "fetch_approval_spec"]);
        // display popover
        await click(target, 'button[name="someMethod"] .o_web_studio_approval');
        assert.containsOnce(target, ".o-approval-popover");
        const popover = target.querySelector(".o-approval-popover");
        assert.containsOnce(popover, ".o_web_studio_approval_no_entry");
        assert.containsOnce(popover, ".o_web_approval_approve");
        assert.containsOnce(popover, ".o_web_approval_reject");
        assert.containsNone(popover, ".o_web_approval_cancel");
    });

    QUnit.test("approval check", async function (assert) {
        assert.expect(4);

        await makeView({
            type: "form",
            resModel: "partner",
            serverData,
            arch: `<form string="Partners">
                    <sheet>
                        <header>
                            <button type="object" id="mainButton" name="someMethod"
                                     string="Apply Method" studio_approval="True"/>
                        </header>
                        <group>
                            <group style="background-color: red">
                                <field name="display_name"/>
                                <field name="bar"/>
                                <field name="int_field"/>
                            </group>
                        </group>
                    </sheet>
                </form>`,
            resId: 2,
            mockRPC: function (route, args) {
                const rule = {
                    id: 1,
                    group_id: [1, "Internal User"],
                    domain: false,
                    can_validate: true,
                    message: false,
                    exclusive_user: false,
                };
                if (args.method === "get_approval_spec") {
                    assert.step("fetch_approval_spec");
                    return Promise.resolve({
                        rules: [rule],
                        entries: [],
                        groups: [[1, "Internal User"]],
                    });
                } else if (args.method === "check_approval") {
                    assert.step("attempt_action");
                    return Promise.resolve({
                        approved: false,
                        rules: [rule],
                        entries: [],
                    });
                } else if (args.method === "someMethod") {
                    /* the action of the button should not be
                    called, as the approval is refused! if this
                    code is traversed, the test *must* fail!
                    that's why it's not included in the expected count
                    or in the verifySteps call */
                    assert.step("should_not_happen!");
                }
            },
        });

        await click(target, "#mainButton");
        // first render, handle click, rerender after click
        assert.verifySteps(["fetch_approval_spec", "attempt_action", "fetch_approval_spec"]);
    });

    QUnit.test("approval widget basic flow", async function (assert) {
        assert.expect(5);

        patchWithCleanup(session, {
            uid: 42,
        });

        let hasValidatedRule;

        await makeView({
            type: "form",
            resModel: "partner",
            serverData,
            arch: `<form string="Partners">
                    <sheet>
                        <header>
                            <button type="object=" name="someMethod" string="Apply Method" studio_approval="True"/>
                        </header>
                        <group>
                            <group style="background-color: red">
                                <field name="display_name"/>
                                <field name="bar"/>
                                <field name="int_field"/>
                            </group>
                        </group>
                    </sheet>
                </form>`,
            resId: 2,
            mockRPC: function (route, args) {
                if (args.method === "get_approval_spec") {
                    const spec = {
                        rules: [
                            {
                                id: 1,
                                group_id: [1, "Internal User"],
                                domain: false,
                                can_validate: true,
                                message: false,
                                exclusive_user: false,
                            },
                        ],
                        entries: [],
                        groups: [[1, "Internal User"]],
                    };
                    if (hasValidatedRule !== undefined) {
                        spec.entries = [
                            {
                                id: 1,
                                approved: hasValidatedRule,
                                user_id: [42, "Some rando"],
                                write_date: "2020-04-07 12:43:48",
                                rule_id: [1, "someMethod/partner (Internal User)"],
                                model: "partner",
                                res_id: 2,
                            },
                        ];
                    }
                    return Promise.resolve(spec);
                } else if (args.method === "set_approval") {
                    hasValidatedRule = args.kwargs.approved;
                    assert.step(hasValidatedRule ? "approve_rule" : "reject_rule");
                    return Promise.resolve(true);
                } else if (args.method === "delete_approval") {
                    hasValidatedRule = undefined;
                    assert.step("delete_approval");
                    return Promise.resolve(true);
                }
            },
        });

        // display popover and validate a rule, then cancel, then reject
        await click(target, 'button[name="someMethod"] .o_web_studio_approval');
        assert.containsOnce(target, ".o_popover");
        await click(target, ".o_popover button.o_web_approval_approve");
        await nextTick();
        await click(target, ".o_popover button.o_web_approval_cancel");
        await click(target, ".o_popover button.o_web_approval_reject");
        assert.verifySteps(["approve_rule", "delete_approval", "reject_rule"]);
    });
    QUnit.test("approval widget basic flow with domain rule", async function (assert) {
        assert.expect(3);

        serverData.views = {
            "partner,false,form": `
            <form>
                <button type="object=" name="someMethod" string="Apply Method" studio_approval="True"/>
            </form>`,
            "partner,false,list": '<tree><field name="display_name"/></tree>',
            "partner,false,search": "<search></search>",
        };

        serverData.actions = {
            1: {
                id: 1,
                name: "Partner",
                res_model: "partner",
                type: "ir.actions.act_window",
                views: [
                    [false, "list"],
                    [false, "form"],
                ],
            },
        };

        let index = 0;
        const recordIds = [1, 2, 3];
        const mockRPC = (route, args) => {
            const rule = {
                id: index,
                group_id: [1, "Internal User"],
                domain: false,
                can_validate: true,
                message: false,
                exclusive_user: false,
            };
            if (args.method === "get_approval_spec") {
                assert.strictEqual(recordIds[index++], args.kwargs.res_id);
                const spec = {
                    rules: [rule],
                    entries: [],
                    groups: [[1, "Internal User"]],
                };
                return Promise.resolve(spec);
            }
        };
        const webClient = await createWebClient({ serverData, mockRPC });
        await doAction(webClient, 1);
        await click(target.querySelector(".o_data_row .o_data_cell"));
        await click(target.querySelector(".o_pager_next"));
        await click(target, 'button[name="someMethod"] .o_web_studio_approval');
        await click(target.querySelector(".o_pager_next"));
        await click(target, 'button[name="someMethod"] .o_web_studio_approval');
    });

    QUnit.test("approval on new record: save before check", async function (assert) {
        serverData.actions = {
            1: {
                id: 1,
                name: "Partner",
                res_model: "partner",
                type: "ir.actions.act_window",
                views: [[false, "form"]],
            },
        };

        const mockRPC = (route, args) => {
            const rule = {
                id: 1,
                group_id: [1, "Internal User"],
                domain: false,
                can_validate: true,
                message: false,
                exclusive_user: false,
            };
            if (args.method === "create") {
                assert.step("create");
            }
            if (args.method === "check_approval") {
                assert.step(`check_approval: ${JSON.stringify(args.args)}`);

                return Promise.resolve({
                    approved: false,
                    rules: [rule],
                    entries: [],
                });
            }
            if (args.method === "get_approval_spec") {
                assert.step(
                    `get_approval_spec: resId: ${args.kwargs.res_id} ; ${JSON.stringify(args.args)}`
                );
                const spec = {
                    rules: [rule],
                    entries: [],
                    groups: [[1, "Internal User"]],
                };
                return Promise.resolve(spec);
            }

            if (args.method === "someMethod") {
                assert.step("button method executed");
            }
        };

        await makeView({
            serverData,
            mockRPC,
            type: "form",
            resModel: "partner",
            arch: `<form>
                <button type="object=" name="someMethod" string="Apply Method" studio_approval="True"/>
            </form>`,
        });

        assert.verifySteps(['get_approval_spec: resId: false ; ["partner","someMethod",false]']);
        await click(target, 'button[name="someMethod"]');
        assert.verifySteps([
            "create",
            'check_approval: ["partner",4,"someMethod",false]',
            'get_approval_spec: resId: 4 ; ["partner","someMethod",false]',
        ]);
    });

    QUnit.test("approval on existing record: save before check", async function (assert) {
        serverData.actions = {
            1: {
                id: 1,
                name: "Partner",
                res_model: "partner",
                type: "ir.actions.act_window",
                views: [[false, "form"]],
            },
        };

        const mockRPC = (route, args) => {
            const rule = {
                id: 1,
                group_id: [1, "Internal User"],
                domain: false,
                can_validate: true,
                message: false,
                exclusive_user: false,
            };
            if (args.method === "write") {
                assert.step("write");
            }
            if (args.method === "check_approval") {
                assert.step(`check_approval: ${JSON.stringify(args.args)}`);

                return Promise.resolve({
                    approved: false,
                    rules: [rule],
                    entries: [],
                });
            }
            if (args.method === "get_approval_spec") {
                assert.step(
                    `get_approval_spec: resId: ${args.kwargs.res_id} ; ${JSON.stringify(args.args)}`
                );
                const spec = {
                    rules: [rule],
                    entries: [],
                    groups: [[1, "Internal User"]],
                };
                return Promise.resolve(spec);
            }

            if (args.method === "someMethod") {
                assert.step("button method executed");
            }
        };

        await makeView({
            serverData,
            mockRPC,
            type: "form",
            resModel: "partner",
            arch: `<form>
                <button type="object=" name="someMethod" string="Apply Method" studio_approval="True"/>
                <field name="int_field"/>
            </form>`,
            resId: 1,
        });

        await editInput(target, ".o_field_widget[name=int_field] input", "10");

        assert.verifySteps(['get_approval_spec: resId: 1 ; ["partner","someMethod",false]']);
        await click(target, 'button[name="someMethod"]');
        assert.verifySteps([
            "write",
            'check_approval: ["partner",1,"someMethod",false]',
            'get_approval_spec: resId: 1 ; ["partner","someMethod",false]',
        ]);
    });

    QUnit.test("approval continues to sync after a component has been destroyed", async function (assert) {
        /* This uses two exclusive buttons. When one is displayed, the other is not.
        When clicking on the first button, this changes the int_field value which
        then hides the first button and display the second one */
        const mockRPC = (route, args) => {
            const rule = {
                id: 1,
                group_id: [1, "Internal User"],
                domain: false,
                can_validate: true,
                message: false,
                exclusive_user: false,
            };
            if (args.method === "check_approval") {
                return Promise.resolve({
                    approved: true,
                    rules: [rule],
                    entries: [],
                });
            }
            if (args.method === "get_approval_spec") {
                const spec = {
                    rules: [rule],
                    entries: [],
                    groups: [[1, "Internal User"]],
                };
                return Promise.resolve(spec);
            }

            if (args.method === "someMethod") {
                serverData.models.partner.records[0].int_field = 1;
                return true;
            }

            if (args.method === "otherMethod") {
                return true;
            }
        };

        await makeView({
            serverData,
            mockRPC,
            type: "form",
            resModel: "partner",
            arch: `<form>
                <button type="object" name="someMethod" string="Apply Method" attrs="{'invisible': [('int_field', '=', 1)]}" studio_approval="True"/>
                <button type="object" name="otherMethod" string="Other Method" attrs="{'invisible': [('int_field', '!=', 1)]}" studio_approval="True"/>
                <field name="int_field"/>
            </form>`,
            resId: 1,
        });

        await click(target, 'button[name="someMethod"]');
        assert.containsNone(target, 'button[name="otherMethod"] .o_web_studio_approval .fa-circle-o-notch.fa-spin');
        assert.containsOnce(target, 'button[name="otherMethod"] .o_web_studio_approval .o_web_studio_approval_avatar');
    });
});
