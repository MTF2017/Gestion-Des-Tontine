from odoo import models, fields, api
from odoo.exceptions import ValidationError

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
    national_id = fields.Char(
        string="Numéro CNI",
        size=13,
        help="Numéro de la Carte Nationale d'Identité (13 chiffres)"
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
    _sql_constraints = [
        ('national_id_unique', 'unique(national_id)', 'Ce numéro CNI est déjà enregistré pour un autre membre.')
    ]

    @api.constrains("national_id")
    def _check_national_id_format(self):
        for member in self:
            if member.national_id:
                if not member.national_id.isdigit():
                    raise ValidationError("Le numéro CNI ne doit contenir que des chiffres.")
                if len(member.national_id) != 13:
                    raise ValidationError("Le numéro CNI doit contenir exactement 13 chiffres.")

    @api.depends("subscription_ids")
    def _compute_subscription_count(self):
        for member in self:
            member.subscription_count = len(member.subscription_ids)

    @api.depends("subscription_ids.penalty_count")
    def _compute_penalty_count(self):
        for member in self:
            member.penalty_count = sum(member.subscription_ids.mapped("penalty_count"))

    