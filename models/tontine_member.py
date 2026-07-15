from odoo import models, fields, api

class TontineMember(models.Model):
    _name = "tontine.member"
    _description = "Membre tontine"
    _rec_name = "name"

    name = fields.Char(
        related="partner_id.name",
        store=True,
        string="Nom"
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact",
        required=True
    )
    phone = fields.Char(
        related="partner_id.phone"
    )
    photo = fields.Image(
        string="Photo"
    )
    join_date = fields.Date(
        default=fields.Date.today
    )
    state = fields.Selection(
        [
            ('active', 'Actif'),
            ('suspended', 'Suspendu')
        ],
        default="active"
    )
    subscription_ids = fields.One2many(
        "tontine.subscription", "member_id", string="Adhésions"
    )
    subscription_count = fields.Integer(
        string="Nombre de tontines",
        compute="_compute_subscription_count",
        store=True
    )
    penalty_count = fields.Integer(
        string="Nombre de pénalités",
        compute="_compute_penalty_count",
        store=True
    )

    @api.depends("subscription_ids")
    def _compute_subscription_count(self):
        for member in self:
            member.subscription_count = len(member.subscription_ids)

    @api.depends("subscription_ids.penalty_count")
    def _compute_penalty_count(self):
        for member in self:
            member.penalty_count = sum(member.subscription_ids.mapped("penalty_count"))

    