from odoo import models, fields, api


class TontinePayment(models.Model):
    _name = "tontine.payment"
    _description = "Cotisation"
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
    member_id = fields.Many2one(
        "tontine.member",
        string="Membre",
        required=True
    )
    available_member_ids = fields.Many2many(
        "tontine.member",
        compute="_compute_available_member_ids",
        string="Membres disponibles"
    )
    subscription_id = fields.Many2one(
        "tontine.subscription",
        string="Adhésion",
        compute="_compute_subscription_id",
        store=True,
        readonly=True
    )
    date = fields.Date(default=fields.Date.today)
    amount = fields.Float(string="Montant payé")
    expected_amount = fields.Float(string="Montant attendu")
    penalty = fields.Float(string="Pénalité")
    state = fields.Selection(
        [
            ('draft', 'En attente'),
            ('paid', 'Payé'),
            ('late', 'Retard')
        ],
        default="draft"
    )
    frequency = fields.Selection(
        related="group_id.frequency",
        string="Fréquence",
        store=True,
        readonly=True
    )
    period_label = fields.Char(
        string="Période",
        compute="_compute_period_label",
        store=True
    )

    @api.depends("group_id")
    def _compute_available_member_ids(self):
        for payment in self:
            if payment.group_id:
                subscriptions = self.env["tontine.subscription"].search([
                    ("group_id", "=", payment.group_id.id)
                ])
                payment.available_member_ids = subscriptions.mapped("member_id")
            else:
                payment.available_member_ids = False

    @api.onchange("group_id")
    def _onchange_group_id(self):
        if self.member_id and self.member_id.id not in self.available_member_ids.ids:
            self.member_id = False
        if self.group_id:
            self.expected_amount = self.group_id.amount
            self.amount = self.group_id.amount
        return {"domain": {"member_id": [("id", "in", self.available_member_ids.ids)]}}

    @api.depends("group_id", "member_id")
    def _compute_subscription_id(self):
        for payment in self:
            if payment.group_id and payment.member_id:
                subscription = self.env["tontine.subscription"].search([
                    ("group_id", "=", payment.group_id.id),
                    ("member_id", "=", payment.member_id.id),
                ], limit=1)
                payment.subscription_id = subscription
            else:
                payment.subscription_id = False

    @api.depends("date", "frequency")
    def _compute_period_label(self):
        for payment in self:
            if not payment.date:
                payment.period_label = False
                continue
            if payment.frequency == "monthly":
                payment.period_label = payment.date.strftime("%Y-%m")
            elif payment.frequency == "weekly":
                iso_year, iso_week, _ = payment.date.isocalendar()
                payment.period_label = f"{iso_year}-S{iso_week:02d}"
            elif payment.frequency == "daily":
                payment.period_label = payment.date.strftime("%Y-%m-%d")
            else:
                payment.period_label = False

    @api.depends("subscription_id", "date")
    def _compute_name(self):
        for payment in self:
            sub_name = payment.subscription_id.name or ""
            date_str = payment.date.strftime("%d/%m/%Y") if payment.date else ""
            payment.name = f"{sub_name} - {date_str}" if sub_name and date_str else (sub_name or "Nouvelle cotisation")
    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        for payment in payments:
            if payment.state == "paid":
                existing = self.env["tontine.cash"].search([("payment_id", "=", payment.id)], limit=1)
                if not existing:
                    self.env["tontine.cash"].create({
                        "group_id": payment.group_id.id,
                        "member_id": payment.member_id.id,
                        "payment_id": payment.id,
                        "date": payment.date,
                        "move_type": "in",
                        "source": "contribution",
                        "amount": payment.amount,
                        "description": f"Cotisation de {payment.member_id.name}",
                    })
        return payments
    def write(self, vals):
        result = super().write(vals)
        if vals.get("state") == "paid":
            for payment in self:
                existing = self.env["tontine.cash"].search([("payment_id", "=", payment.id)], limit=1)
                if not existing:
                    self.env["tontine.cash"].create({
                        "group_id": payment.group_id.id,
                        "member_id": payment.member_id.id,
                        "payment_id": payment.id,
                        "date": payment.date,
                        "move_type": "in",
                        "source": "contribution",
                        "amount": payment.amount,
                        "description": f"Cotisation de {payment.member_id.name}",
                    })
        return result
    def unlink(self):
        cash_moves = self.env["tontine.cash"].search([("payment_id", "in", self.ids)])
        cash_moves.unlink()
        return super().unlink()