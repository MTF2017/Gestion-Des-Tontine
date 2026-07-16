import random
from odoo import models, fields, api
from odoo.exceptions import UserError


class TontineGroup(models.Model):
    _name = "tontine.group"
    _description = "Tontine"

    name = fields.Char(
        string="Nom de la tontine",
        required=True
    )

    manager_id = fields.Many2one(
        "res.users",
        string="Responsable"
    )

    amount = fields.Float(
        string="Montant cotisation",
        required=True
    )

    frequency = fields.Selection(
        [
            ('daily', 'Quotidienne'),
            ('weekly', 'Hebdomadaire'),
            ('monthly', 'Mensuelle')
        ],
        string="Fréquence",
        default="monthly"
    )

    start_date = fields.Date(
        string="Date début"
    )

    end_date = fields.Date(
        string="Date fin"
    )

    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('active', 'Active'),
            ('closed', 'Clôturée')
        ],
        default="draft"
    )

    member_ids = fields.One2many(
        "tontine.subscription",
        "group_id",
        string="Participants"
    )
    is_manager = fields.Boolean(string="Est responsable",compute="_compute_is_manager")

    group_penalty_count = fields.Integer(
        string="Total pénalités",
        compute="_compute_group_penalty_count",
        store=True
    )

    @api.depends("member_ids.penalty_count")
    def _compute_group_penalty_count(self):
        for group in self:
            group.group_penalty_count = sum(group.member_ids.mapped("penalty_count"))

    @api.depends("manager_id")
    def _compute_is_manager(self):
        for group in self:
            group.is_manager = group.manager_id.id == self.env.uid

    def action_activate(self):
        for group in self:
            if not group.member_ids:
                raise UserError("Impossible d'activer une tontine sans membres inscrits.")
            group._draw_order()
            group.state = "active"

    def action_close(self):
        self.state = "closed"

    def action_reset_draft(self):
        for group in self:
            if group.manager_id.id != self.env.uid:
                raise UserError(
                    f"Seul le responsable de la tontine « {group.name} » "
                    "peut la remettre en brouillon."
                )
            group.state = "draft"

    def _draw_order(self):
        self.ensure_one()
        subscriptions = self.member_ids
        orders = list(range(1, len(subscriptions) + 1))
        random.shuffle(orders)
        for subscription, order in zip(subscriptions, orders):
            subscription.order = order
    @api.model
    def get_dashboard_global_data(self):
        groups = self.search([])
        cash_moves = self.env["tontine.cash"].search([])
        total_in = sum(cash_moves.filtered(lambda m: m.move_type == "in").mapped("amount"))
        total_out = sum(cash_moves.filtered(lambda m: m.move_type == "out").mapped("amount"))

        groups_summary = []
        for g in groups:
            g_in = sum(cash_moves.filtered(lambda m: m.move_type == "in" and m.group_id.id == g.id).mapped("amount"))
            g_out = sum(cash_moves.filtered(lambda m: m.move_type == "out" and m.group_id.id == g.id).mapped("amount"))
            groups_summary.append({
                "id": g.id,
                "name": g.name,
                "state": g.state,
                "frequency": g.frequency,
                "members": len(g.member_ids),
                "balance": g_in - g_out,
            })

        return {
            "total_groups": len(groups),
            "draft_groups": len(groups.filtered(lambda g: g.state == "draft")),
            "active_groups": len(groups.filtered(lambda g: g.state == "active")),
            "closed_groups": len(groups.filtered(lambda g: g.state == "closed")),
            "total_members": self.env["tontine.member"].search_count([]),
            "total_in": total_in,
            "total_out": total_out,
            "balance": total_in - total_out,
            "late_payments": self.env["tontine.payment"].search_count([("state", "=", "late")]),
            "groups": groups_summary,
        }
    def get_dashboard_group_data(self):
        self.ensure_one()
        subs = self.member_ids
        payments = self.env["tontine.payment"].search([("group_id", "=", self.id)])
        cash = self.env["tontine.cash"].search([("group_id", "=", self.id)])
        distributions = self.env["tontine.distribution"].search([("group_id", "=", self.id)])
        penalties = self.env["tontine.penalty"].search([("subscription_id.group_id", "=", self.id)])
        total_in = sum(cash.filtered(lambda m: m.move_type == "in").mapped("amount"))
        total_out = sum(cash.filtered(lambda m: m.move_type == "out").mapped("amount"))

        members_data = []
        for s in subs:
            member_distribution = distributions.filtered(
                lambda d: d.beneficiary_id.id == s.member_id.id
            )
            if member_distribution.filtered(lambda d: d.state == "done"):
                dist_status = "done"
                dist = member_distribution.filtered(lambda d: d.state == "done")[0]
                dist_amount = dist.amount
                dist_date = str(dist.planned_date) if dist.planned_date else ""
            else:
                dist_status = "not_done"
                dist_amount = 0
                dist_date = ""

            members_data.append({
                "id": s.id,
                "name": s.member_id.name,
                "order": s.order,
                "distribution_status": dist_status,
                "distribution_amount": dist_amount,
                "distribution_date": dist_date,
            })

        return {
            "name": self.name,
            "state": self.state,
            "frequency": self.frequency,
            "members_count": len(subs),
            "expected_total": sum(payments.mapped("expected_amount")),
            "paid_total": sum(payments.mapped("amount")),
            "late_count": len(payments.filtered(lambda p: p.state == "late")),
            "paid_count": len(payments.filtered(lambda p: p.state == "paid")),
            "distributions_done": len(distributions.filtered(lambda d: d.state == "done")),
            "distributions_planned": len(distributions.filtered(lambda d: d.state == "planned")),
            "penalties_total": sum(penalties.mapped("amount")),
            "cash_in": total_in,
            "cash_out": total_out,
            "balance": total_in - total_out,
            "members": members_data,
        }