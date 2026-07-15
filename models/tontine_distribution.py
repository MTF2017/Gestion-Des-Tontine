from odoo import models, fields, api


class TontineDistribution(models.Model):
    _name = "tontine.distribution"
    _description = "Distribution tontine"
    _rec_name = "name"

    name = fields.Char(
        string="Référence",
        compute="_compute_name",
        store=True
    )
    group_id = fields.Many2one(
        "tontine.group",
        string="Tontine",
        required=True
    )
    beneficiary_id = fields.Many2one(
        "tontine.member",
        string="Bénéficiaire",
        required=True
    )
    available_beneficiary_ids = fields.Many2many(
        "tontine.member",
        compute="_compute_available_beneficiary_ids",
        string="Bénéficiaires disponibles"
    )
    order = fields.Integer(
        string="Ordre de passage"
    )
    amount = fields.Float(
        string="Montant distribué"
    )
    planned_date = fields.Date(
        string="Date",
        default=fields.Date.today
    )
    
    state = fields.Selection(
        [
            ('planned', 'Non Effectuée'),
            ('done', 'Effectuée')
        ],
        string="Etat",
        default="planned"
    )

    @api.depends("group_id", "beneficiary_id", "planned_date")
    def _compute_name(self):
        for dist in self:
            group_name = dist.group_id.name or ""
            member_name = dist.beneficiary_id.name or ""
            date_str = dist.planned_date.strftime("%d/%m/%Y") if dist.planned_date else ""
            if member_name and group_name:
                dist.name = f"{member_name} - {group_name} ({date_str})" if date_str else f"{member_name} - {group_name}"
            else:
                dist.name = member_name or group_name or "Nouvelle distribution"
    
    @api.depends("group_id")
    def _compute_available_beneficiary_ids(self):
        for dist in self:
            if dist.group_id:
                already_distributed = self.env["tontine.distribution"].search([
                    ("group_id", "=", dist.group_id.id),
                    ("state", "=", "done"),
                    ("id", "!=", dist.id if dist.id else False),
                ]).mapped("beneficiary_id").ids
                all_members = dist.group_id.member_ids.mapped("member_id").ids
                remaining = [m for m in all_members if m not in already_distributed]
                dist.available_beneficiary_ids = [(6, 0, remaining)]
            else:
                dist.available_beneficiary_ids = [(6, 0, [])]

    @api.onchange("group_id")
    def _onchange_group_id(self):
        if self.group_id:
            nb_members = len(self.group_id.member_ids)
            self.amount = self.group_id.amount * nb_members

            # Exclure les membres ayant DÉJÀ une distribution (peu importe son état)
            already_distributed = self.env["tontine.distribution"].search([
                ("group_id", "=", self.group_id.id),
            ]).mapped("beneficiary_id").ids

            next_subscription = self.group_id.member_ids.filtered(
                lambda s: s.member_id.id not in already_distributed
            ).sorted(key=lambda s: s.order)[:1]

            if next_subscription:
                self.beneficiary_id = next_subscription.member_id
                self.order = next_subscription.order
            else:
                self.beneficiary_id = False
                self.order = 0
        else:
            self.beneficiary_id = False
            self.order = 0

        return {"domain": {"beneficiary_id": [("id", "in", self.available_beneficiary_ids.ids)]}}
    @api.depends("group_id", "beneficiary_id", "planned_date")
    def _compute_name(self):
        for dist in self:
            group_name = dist.group_id.name or ""
            member_name = dist.beneficiary_id.name or ""
            date_str = dist.planned_date.strftime("%d/%m/%Y") if dist.planned_date else ""
            if member_name and group_name:
                dist.name = f"{member_name} - {group_name} ({date_str})" if date_str else f"{member_name} - {group_name}"
            else:
                dist.name = member_name or group_name or "Nouvelle distribution"
    @api.model_create_multi
    def create(self, vals_list):
        distributions = super().create(vals_list)
        for dist in distributions:
            if dist.state == "done":
                existing = self.env["tontine.cash"].search([("distribution_id", "=", dist.id)], limit=1)
                if not existing:
                    self.env["tontine.cash"].create({
                        "group_id": dist.group_id.id,
                        "member_id": dist.beneficiary_id.id,
                        "distribution_id": dist.id,
                        "date": dist.planned_date or fields.Date.today(),
                        "move_type": "out",
                        "source": "distribution",
                        "amount": dist.amount,
                        "description": f"Distribution à {dist.beneficiary_id.name}",
                    })
        return distributions

    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") == "done":
            for dist in self:
                existing = self.env["tontine.cash"].search([("distribution_id", "=", dist.id)], limit=1)
                if not existing:
                    self.env["tontine.cash"].create({
                        "group_id": dist.group_id.id,
                        "member_id": dist.beneficiary_id.id,
                        "distribution_id": dist.id,
                        "date": dist.planned_date or fields.Date.today(),
                        "move_type": "out",
                        "source": "distribution",
                        "amount": dist.amount,
                        "description": f"Distribution à {dist.beneficiary_id.name}",
                    })
        return result
    def unlink(self):
        cash_moves = self.env["tontine.cash"].search([("distribution_id", "in", self.ids)])
        cash_moves.unlink()
        return super().unlink()