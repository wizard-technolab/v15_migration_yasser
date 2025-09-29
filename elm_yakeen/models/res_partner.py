import logging  # Importing logging to log messages
from odoo import api, models, fields, _  # Importing necessary Odoo modules and decorators
from odoo.exceptions import ValidationError  # Importing ValidationError to raise validation errors

_logger = logging.getLogger(__name__)  # Setting up logging for this module


class res_partner(models.Model):
    _inherit = 'res.partner'  # Inheriting from the 'res.partner' model to extend it
    _description = 'partner data'

    # Define a Many2one relationship to the 'elm.yakeen.person' model
    elm_yakeen_id = fields.Many2one('elm.yakeen.person')

    # Common fields related to 'elm_yakeen_id'
    elm_first_name = fields.Char(related='elm_yakeen_id.first_name')  # First name (related field)
    elm_father_name = fields.Char(related='elm_yakeen_id.father_name')  # Father name (related field)
    elm_grand_father_name = fields.Char(related='elm_yakeen_id.grand_father_name')  # Grandfather name (related field)
    elm_family_name = fields.Char(related='elm_yakeen_id.family_name')  # Family name (related field)
    elm_english_first_name = fields.Char(
        related='elm_yakeen_id.english_first_name')  # English first name (related field)
    elm_english_second_name = fields.Char(
        related='elm_yakeen_id.english_second_name')  # English second name (related field)
    elm_english_third_name = fields.Char(
        related='elm_yakeen_id.english_third_name')  # English third name (related field)
    elm_english_last_name = fields.Char(related='elm_yakeen_id.english_last_name')  # English last name (related field)

    elm_id_expiry_date = fields.Char(compute='_compute_elm_dates')  # ID expiry date (computed field)
    elm_gender = fields.Selection(related='elm_yakeen_id.gender')  # Gender (related field)
    elm_date_of_birth = fields.Char(compute='_compute_elm_dates')  # Date of birth (computed field)

    elm_address_line_ids = fields.One2many(related='elm_yakeen_id.address_line_ids')  # Address lines (related field)

    # Citizen specific fields
    elm_occupation_code = fields.Char(related='elm_yakeen_id.occupation_code')  # Occupation code (related field)

    # Alien specific fields
    elm_sponsor_name = fields.Char(related='elm_yakeen_id.sponsor_name')  # Sponsor name (related field)
    elm_nationality_code = fields.Char(related='elm_yakeen_id.nationality_code')  # Nationality code (related field)
    elm_address_ids = fields.One2many(related='elm_yakeen_id.address_line_ids')  # Address lines (related field)

    # Hijri birth date fields
    hijri_birth_date_day = fields.Integer('Hijri Birth (Day)')  # Hijri birth day
    hijri_birth_date_year = fields.Integer('Hijri Birth (Year)')  # Hijri birth year
    hijri_birth_date_month = fields.Selection([  # Hijri birth month selection
        ('01', '1. Muharram'),
        ('02', '2. Safar'),
        ('03', '3. Rabi al-Awwal'),
        ('04', '4. Rabi al-Thani'),
        ('05', '5. Jumada al-Awwal'),
        ('06', '6. Jumada al-Thani'),
        ('07', '7. Rajab'),
        ('08', '8. Shaban'),
        ('09', '9. Ramadan'),
        ('10', '10. Shawwal'),
        ('11', '11. Dhu al-Qadah'),
        ('12', '12. Dhu al-Hijjah'),
    ], string='Hijri Birth (Month)')

    @api.depends('elm_yakeen_id')
    def _compute_elm_dates(self):
        """
        Compute method to set elm_date_of_birth and elm_id_expiry_date.
        Uses date_of_birth or birth_of_date_hijri for elm_date_of_birth.
        Uses id_expiry_date or id_expiry_date_hijri for elm_id_expiry_date.
        """
        for r in self:
            r.elm_date_of_birth = r.elm_yakeen_id.date_of_birth or r.elm_yakeen_id.birth_of_date_hijri
            r.elm_id_expiry_date = r.elm_yakeen_id.id_expiry_date or r.elm_yakeen_id.id_expiry_date_hijri

    @api.constrains('hijri_birth_date_year')
    def validate_hijri_birth_year(self):
        """
        Constraint to validate the Hijri birth year.
        The year must be between 1317 and 1444.
        Raises a ValidationError if the year is out of this range.
        """
        for r in self:
            if not r.hijri_birth_date_year:
                continue
            if r.hijri_birth_date_year < 1317 or r.hijri_birth_date_year > 1444:
                raise ValidationError(_('Please enter a valid Hijri Birth (Year)'))

    def action_verify_elm_yakeen(self):
        """
        Action to verify ELM Yakeen.
        Calls add_result on the related elm.yakeen.person.
        """
        self.ensure_one()  # Ensures that only one record is being processed
        self.env['elm.yakeen.person'].add_result(self)

    def action_reset(self):
        """
        Action to reset the ELM Yakeen.
        Sets the related elm.yakeen.person as inactive and unlinks the relation.
        """
        self.elm_yakeen_id.active = False
        self.elm_yakeen_id = False
