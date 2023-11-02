/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
import {
    Component,
    onMounted,
    onPatched,
    onWillDestroy,
    onWillPatch,
    onWillStart,
} from "@odoo/owl";

let observerId = 0;

export class AbstractBehavior extends Component {
    setup() {
        super.setup();
        this.setupAnchor();
        this.knowledgeCommandsService = useService('knowledgeCommandsService');
        this.observerId = observerId++;
        if (!this.props.readonly) {
            onWillStart(() => {
                this.editor.observerUnactive(`knowledge_behavior_id_${this.observerId}`);
            });
            onWillPatch(() => {
                this.editor.observerUnactive(`knowledge_behavior_id_${this.observerId}`);
            });
            onMounted(() => {
                this.editor.idSet(this.props.anchor);
                this.editor.observerActive(`knowledge_behavior_id_${this.observerId}`);
            });
            onPatched(() => {
                this.editor.idSet(this.props.anchor);
                this.editor.observerActive(`knowledge_behavior_id_${this.observerId}`);
            });
            onWillDestroy(() => {
                this.editor.observerActive(`knowledge_behavior_id_${this.observerId}`);
            });
        }
    }

    /**
     * This method is used to ensure that the correct attributes are set
     * on the anchor of the Behavior. Attributes could be incorrect for the
     * following reasons: cleaned by the sanitization (frontend or backend),
     * attributes from a previous Odoo version, attributes from a drop/paste
     * of a Behavior which was in another state (i.e. from readonly to editable)
     */
    setupAnchor() {
        if (!this.props.readonly) {
            this.props.anchor.setAttribute('contenteditable', 'false');
        }
    }

    get editor () {
        return this.props.wysiwyg ? this.props.wysiwyg.odooEditor : undefined;
    }
}

AbstractBehavior.props = {
    readonly: { type: Boolean },
    anchor: { type: Element },
    wysiwyg: { type: Object, optional: true},
    record: { type: Object },
    root: { type: Element },
};
