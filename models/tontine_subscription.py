from odoo import models, fields, api


class TontineSubscription(models.Model):
    _name = "tontine.subscription"
    _description = "Adhésion tontine"
    _rec_name = "name"

    name = fields.Char(
        string="Nom",
        compute="_compute_name",
        store=True
    )
    group_id = fields.Many2one("tontine.group", string="Tontine")
    member_id = fields.Many2one("tontine.member", string="Membre")
    available_member_ids = fields.Many2many(
        "tontine.member",
        compute="_compute_available_member_ids",
        string="Membres disponibles"
    )
    join_date = fields.Date(default=fields.Date.today)
    order = fields.Integer(string="Ordre de passage")

    payment_ids = fields.One2many("tontine.payment", "subscription_id", string="Paiements")
    payment_status = fields.Selection(
        [
            ('paid', 'À jour'),
            ('late', 'En retard'),
            ('none', 'Aucun paiement')
        ],
        string="Statut paiement",
        compute="_compute_payment_status",
        store=True
    )
    penalty_ids = fields.One2many("tontine.penalty", "subscription_id", string="Pénalités")
    penalty_count = fields.Integer(
        string="Nombre de pénalités",
        compute="_compute_penalty_count",
        store=True
    )

    @api.depends("group_id")
    def _compute_available_member_ids(self):
        for sub in self:
            if sub.group_id:
                already_subscribed = self.env["tontine.subscription"].search([
                    ("group_id", "=", sub.group_id.id),
                    ("id", "!=", sub.id if sub.id else False),
                ]).mapped("member_id").ids
                all_members = self.env["tontine.member"].search([]).ids
                remaining = [m for m in all_members if m not in already_subscribed]
                sub.available_member_ids = [(6, 0, remaining)]
            else:
                sub.available_member_ids = [(6, 0, [])]

    @api.onchange("group_id")
    def _onchange_group_id(self):
        if self.member_id and self.member_id.id not in self.available_member_ids.ids:
            self.member_id = False
        return {"domain": {"member_id": [("id", "in", self.available_member_ids.ids)]}}

    @api.depends("penalty_ids")
    def _compute_penalty_count(self):
        for sub in self:
            sub.penalty_count = len(sub.penalty_ids)

    @api.depends("member_id", "group_id")
    def _compute_name(self):
        for sub in self:
            member_name = sub.member_id.name or ""
            group_name = sub.group_id.name or ""
            sub.name = f"{member_name} - {group_name}" if member_name and group_name else (member_name or group_name or "Nouvelle adhésion")

    @api.depends("payment_ids.state")
    def _compute_payment_status(self):
        for sub in self:
            states = sub.payment_ids.mapped("state")
            if not states:
                sub.payment_status = "none"
            elif "late" in states:
                sub.payment_status = "late"
            elif all(s == "paid" for s in states):
                sub.payment_status = "paid"
            else:
                sub.payment_status = "none"