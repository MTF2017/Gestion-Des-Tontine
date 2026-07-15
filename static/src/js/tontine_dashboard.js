/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TontineDashboard extends Component {
    static template = "gestion_tontine.TontineDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            loading: true,
            view: "global",
            data: null,
            groupData: null,
        });
        onWillStart(async () => {
            await this.loadGlobal();
        });
    }

    async loadGlobal() {
        this.state.loading = true;
        this.state.view = "global";
        this.state.data = await this.orm.call("tontine.group", "get_dashboard_global_data", []);
        this.state.loading = false;
    }

    async openGroup(groupId) {
        this.state.loading = true;
        this.state.groupData = await this.orm.call("tontine.group", "get_dashboard_group_data", [[groupId]]);
        this.state.view = "detail";
        this.state.loading = false;
    }

    backToGlobal() {
        this.state.view = "global";
    }

    formatAmount(value) {
        return new Intl.NumberFormat("fr-FR").format(Math.round(value || 0)) + " FCFA";
    }
}

registry.category("actions").add("tontine_dashboard", TontineDashboard);