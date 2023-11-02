/** @odoo-module **/

import { registry } from "@web/core/registry";
import { makeView, setupViewRegistries } from "@web/../tests/views/helpers";
import { patchWithCleanup, triggerEvent } from '@web/../tests/helpers/utils';
import { makeFakeDialogService } from '@web/../tests/helpers/mock_services';
import Wysiwyg from 'web_editor.wysiwyg';
import { insertText } from '@web_editor/js/editor/odoo-editor/test/utils'
import { setSelection } from '@web_editor/js/editor/odoo-editor/src/utils/utils';

const linkUrl = window.location.origin + '/book/123';
const serviceRegistry = registry.category("services");
let serverData;
let wysiwyg;

function onMount() {
    const editor = wysiwyg.odooEditor;
    const editable = editor.editable;
    const originalContent = editable.innerHTML;
    editor.testMode = true;
    return { editor, editable, originalContent };
}

function assertHistorySteps(assert, editable, originalContent) {
    const currentContent = editable.innerHTML;
    wysiwyg.odooEditor.historyUndo();
    assert.strictEqual(editable.innerHTML, originalContent);
    wysiwyg.odooEditor.historyRedo();
    assert.strictEqual(editable.innerHTML, currentContent);
}

QUnit.module('appointment.wysiwyg', {
    before: function () {
        serverData = {
            models: {
                note: {
                    fields: {
                        display_name: {
                            string: "Displayed name",
                            type: "char"
                        },
                        body: {
                            string: "Message",
                            type: "html"
                        },
                    },
                    records: [{
                        id: 1,
                        display_name: "first record",
                        body: '<p></p>',
                    }, {
                        id: 2,
                        display_name: "second record",
                        body: '<p><a href="http://odoo.com">Existing link</a></p>',
                    }],
                },
            },
        };
    },
    beforeEach: function () {
        setupViewRegistries();
        serviceRegistry.add(
            'dialog',
            makeFakeDialogService((dialogClass, props) => props.insertLink(linkUrl)),
            { force: true },
        );
        patchWithCleanup(Wysiwyg.prototype, {
            init: function () {
                this._super.apply(this, arguments);
                wysiwyg = this;
            }
        });
    }
}, function () {

    QUnit.test('Insert link with "/Calendar"', async function (assert) {
        assert.expect(3);

        await makeView({
            type: 'form',
            serverData,
            resModel: 'note',
            arch: '<form>' +
                '<field name="body" widget="html" style="height: 100px"/>' +
                '</form>',
            resId: 1,
        });
        const { editor, editable, originalContent } = onMount();

        // Type powerbox command + 'Enter'
        setSelection(editable.querySelector('p'), 0);
        await insertText(editor, '/Calendar');
        await triggerEvent(editable, null, 'keydown', { key: 'Enter' });

        assert.strictEqual(editable.innerHTML,
            `<p><a href="${window.location.origin}/appointment">Our Appointment Types</a></p>`);

        assertHistorySteps(assert, editable, originalContent);
    });

    QUnit.test('Insert link with "/Appointment"', async function (assert) {
        assert.expect(3);

        await makeView({
            type: 'form',
            serverData,
            resModel: 'note',
            arch: '<form>' +
                '<field name="body" widget="html" style="height: 100px"/>' +
                '</form>',
            resId: 1,
        });
        const { editor, editable, originalContent } = onMount();

        // Type powerbox command + 'Enter'
        setSelection(editable.querySelector('p'), 0);
        await insertText(editor, '/Appointment');
        await triggerEvent(editable, null, 'keydown', { key: 'Enter' });

        assert.strictEqual(editable.innerHTML,
            `<p><a href="${linkUrl}">Schedule an Appointment</a></p>`);

        assertHistorySteps(assert, editable, originalContent);
    });

    QUnit.test('Replace existing link with "/Calendar" link', async function (assert) {
        assert.expect(3);

        await makeView({
            type: 'form',
            serverData,
            resModel: 'note',
            arch: '<form>' +
                '<field name="body" widget="html" style="height: 100px"/>' +
                '</form>',
            resId: 2,
        });
        const { editor, editable, originalContent } = onMount();

        // Place cursor at beginning of link's label
        const p = editable.querySelector('p');
        setSelection(p.firstChild.firstChild, 0);

        // Type powerbox command + 'Enter'
        await insertText(editor, '/Calendar');
        await triggerEvent(editable, null, 'keydown', { key: 'Enter' });

        assert.strictEqual(editable.innerHTML,
            `<p><a href="${window.location.origin}/appointment">Our Appointment Types</a></p>`);

        assertHistorySteps(assert, editable, originalContent);
    });

    QUnit.test('Replace existing link with "/Appointment" link', async function (assert) {
        assert.expect(3);

        await makeView({
            type: 'form',
            serverData,
            resModel: 'note',
            arch: '<form>' +
                '<field name="body" widget="html"/>' +
                '</form>',
            resId: 2,
        });
        const { editor, editable, originalContent } = onMount();

        // Place cursor at beginning of link's label
        const p = editable.querySelector('p');
        setSelection(p.firstChild.firstChild, 0);

        // Type powerbox command + 'Enter'
        await insertText(editor, '/Appointment');
        await triggerEvent(editable, null, 'keydown', { key: 'Enter' });

        assert.strictEqual(editable.innerHTML,
            `<p><a href="${linkUrl}">Schedule an Appointment</a></p>`);

        assertHistorySteps(assert, editable, originalContent);
    });
});
