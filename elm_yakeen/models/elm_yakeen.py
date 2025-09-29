import datetime  # Importing datetime for date manipulations
import logging  # Importing logging to log messages
import os  # Importing os to access environment variables
from zeep import Client as ZeepClient, helpers  # Importing Zeep for SOAP client and helpers
from zeep.exceptions import Fault  # Importing Fault for handling SOAP faults
from zeep.transports import Transport  # Importing Transport for custom transport settings
from requests import Session  # Importing Session for HTTP sessions
from odoo import api, fields, models, _, SUPERUSER_ID  # Importing Odoo modules and decorators
from odoo.exceptions import ValidationError, UserError  # Importing Odoo exceptions

_logger = logging.getLogger(__name__)  # Setting up logging for this module


class elm_yakeen_address(models.Model):
    _name = 'elm.yakeen.address'  # Defining model name
    _description = 'Elm Yakeen Address'  # Defining model description
    _order = "id desc"  # Setting default order by ID descending

    elm_person_id = fields.Many2one('elm.yakeen.person', required=True)  # Many2one relation to 'elm.yakeen.person'
    additional_number = fields.Char()  # Additional number field
    building_number = fields.Char()  # Building number field
    city = fields.Char()  # City field
    district = fields.Char()  # District field
    location_coordinates = fields.Char()  # Location coordinates field
    post_code = fields.Char()  # Post code field
    street_name = fields.Char()  # Street name field
    unit_number = fields.Char()  # Unit number field
    log_id = fields.Char()  # Log ID field

    @api.model
    def create_from_response(self, response, elm_person_id):
        """
        Create address record from API response.
        """
        self.create({
            'elm_person_id': elm_person_id.id,
            'additional_number': response.get('additionalNumber', ''),
            'building_number': response.get('buildingNumber', ''),
            'city': response.get('city', ''),
            'district': response.get('district', ''),
            'location_coordinates': response.get('locationCoordinates', ''),
            'post_code': response.get('postCode', ''),
            'street_name': response.get('streetName', ''),
            'unit_number': response.get('unitNumber', ''),
            'log_id': response.get('logId', ''),
        })


class elm_yakeen_person_common(models.Model):
    _name = 'elm.yakeen.person'  # Defining model name
    _description = 'Elm Yakeen Person'  # Defining model description
    _order = "id desc"  # Setting default order by ID descending

    partner_id = fields.Many2one('res.partner')  # Many2one relation to 'res.partner'
    active = fields.Boolean(default=True)  # Active field with default value True
    first_name = fields.Char()  # First name field
    father_name = fields.Char()  # Father name field
    grand_father_name = fields.Char()  # Grandfather name field
    family_name = fields.Char()  # Family name field
    english_first_name = fields.Char()  # English first name field
    english_second_name = fields.Char()  # English second name field
    english_third_name = fields.Char()  # English third name field
    english_last_name = fields.Char()  # English last name field
    id_expiry_date = fields.Date()  # ID expiry date field
    id_expiry_date_hijri = fields.Char()  # Hijri ID expiry date field
    gender = fields.Selection([  # Gender selection field
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Undefined'),
    ])
    date_of_birth = fields.Date()  # Date of birth field
    birth_of_date_hijri = fields.Char()  # Hijri birth date field
    # Citizen specific fields
    occupation_code = fields.Char()  # Occupation code field
    # Foreigner specific fields
    sponsor_name = fields.Char()  # Sponsor name field
    nationality_code = fields.Char()  # Nationality code field
    address_line_ids = fields.One2many('elm.yakeen.address',
                                       'elm_person_id')  # One2many relation to 'elm.yakeen.address'

    @api.model
    def _parse_date(self, value):
        """
        Parse date from the format dd-MM-yyyy.
        """
        if not value:
            return False
        _logger.info('# parsing date {}'.format(value))
        return datetime.datetime.strptime(value, '%d-%m-%Y')

    def set_values_from_response(self, response):
        """
        Set values from API response.
        """
        self.ensure_one()  # Ensure only one record is being processed
        birth_date_name = 'dateOfBirthH'  # Default birth date key for Hijri
        id_expiry_name = 'idExpiryDate'  # Default ID expiry date key

        if self.partner_id.nationality != 'saudi':  # Change keys for non-Saudis
            birth_date_name = 'dateOfBirthG'
            id_expiry_name = 'iqamaExpiryDateG'

        values = {
            'first_name': response.get('firstName', ''),
            'father_name': response.get('secondName', ' '),
            'grand_father_name': response.get('thirdName', ''),
            'family_name': response.get('lastName', ''),
            'english_first_name': response.get('englishFirstName', ''),
            'english_second_name': response.get('englishSecondName', ''),
            'english_third_name': response.get('englishThirdName', ''),
            'english_last_name': response.get('englishLastName', ''),
            'gender': response.get('gender', ''),
            'occupation_code': response.get('occupationCode', ''),
            'nationality_code': response.get('nationalityCode', ''),
            'sponsor_name': response.get('sponsorName', ''),
        }

        def set_date(date_key, char_key, value):
            """
            Set date fields with parsing.
            """
            try:
                values[date_key] = self._parse_date(value)
            except ValueError:
                values[char_key] = value

        set_date('date_of_birth', 'birth_of_date_hijri', response.get(birth_date_name))
        set_date('id_expiry_date', 'id_expiry_date_hijri', response.get(id_expiry_name))
        self.write(values)

    @api.model
    def raise_already_exists(self):
        """
        Raise a validation error if a result already exists.
        """
        raise ValidationError(_('This partner already has a "Elm & Yakeen" result'))

    @api.model
    def add_result(self, partner):
        """
        Add result from ELM Yakeen API to the partner.
        """
        if partner.elm_yakeen_id:
            self.raise_already_exists()

        response = self.call_elm_api(partner)  # Call the ELM Yakeen API
        result_id = self.create({
            'partner_id': partner.id,
        })
        partner.elm_yakeen_id = result_id
        result_id.set_values_from_response(response)

        addres_response = self.call_elm_address_api(partner).get('addressListList', [])
        for item in addres_response:
            self.env['elm.yakeen.address'].create_from_response(item, result_id)

    @api.constrains('partner_id')
    def validate_partner_id(self):
        """
        Validate that the partner does not have multiple ELM Yakeen results.
        """
        for r in self:
            existing_ids = self.search([('partner_id', '=', r.partner_id.id)])
            if (len(existing_ids) > 1):
                self.raise_already_exists()

    def call_elm_address_api(self, partner):
        """
        Call the ELM Yakeen address API.
        """
        client, auth = self._get_zeep_client()
        birth_date = self._get_birth_date(partner)

        common = {
            'addressLanguage': 'A',
            'dateOfBirth': birth_date,
            'referenceNumber': partner.id,  # Put partner id here
        }
        common.update(auth)

        try:
            if partner.nationality == 'saudi':
                citizenAddressRequest = common.copy()
                citizenAddressRequest.update({
                    'nin': partner.identification_no,
                })
                res = client.service.getCitizenAddressInfo(citizenAddressRequest)
                return helpers.serialize_object(res, dict)
            else:
                alienAddressRequest = common.copy()
                alienAddressRequest.update({
                    'iqamaNumber': partner.identification_no,
                })
                res = client.service.getAlienAddressInfoByIqama(alienAddressRequest)
                return helpers.serialize_object(res, dict)
        except Fault as ex:
            raise UserError(_(ex))
        except Exception as ex:
            raise UserError(_('Elm & Yakeen API failed\n{}').format(ex))

    def _get_zeep_client(self):
        """
        Get Zeep client with authentication details.
        """
        session = Session()
        cert_path = os.getenv('ELM_CERT', False)  # Get certificate path from environment variable
        transport = None
        if cert_path:
            session.verify = cert_path
            transport = Transport(session=session)

        username = os.getenv('ELM_USERNAME', 'Fuel_pilot')  # Get username from environment variable
        password = os.getenv('ELM_PASSWORD', 'Fuel@3335411')  # Get password from environment variable
        charge_code = os.getenv('ELM_CHARGE_CODE', 'PILOT')  # Get charge code from environment variable
        url = os.getenv('ELM_URL',
                        'https://yakeen-piloting.eserve.com.sa/Yakeen4Fuel/Yakeen4Fuel?WSDL')  # Get URL from environment variable

        client = ZeepClient(url, transport=transport)  # Initialize Zeep client
        common = {
            'chargeCode': charge_code,
            'password': password,
            'userName': username,
        }
        return client, common

    def _get_birth_date(self, partner):
        """
        Get the birthdate of the partner.
        """
        birth_date = ''
        if partner.nationality == 'saudi':
            if partner.hijri_birth_date_year and partner.hijri_birth_date_month:
                birth_date = '{}-{}'.format(partner.hijri_birth_date_month, partner.hijri_birth_date_year)
            else:
                raise UserError(_('Please enter Hijri birth date'))
        else:
            if partner.birth_of_date:
                birth_date = fields.Date.from_string(partner.birth_of_date).strftime('%m-%Y')  # Format is MM-yyyy
            else:
                raise UserError(_('Please enter date of birth'))
        return birth_date

    def call_elm_api(self, partner):
        """
        Call the ELM Yakeen API to get partner information.
        """
        birth_date = self._get_birth_date(partner)
        client, auth = self._get_zeep_client()
        common = {
            'referenceNumber': partner.id,  # Put partner id here
        }
        common.update(auth)

        try:
            if partner.nationality == 'saudi':
                citizenInfoRequest = common.copy()
                citizenInfoRequest.update({
                    'nin': partner.identification_no,
                    'dateOfBrith': birth_date,  # NOTE: there is a typo in the dateOfBrith in the API
                })
                res = client.service.getCitizenInfo(citizenInfoRequest)
                return helpers.serialize_object(res, dict)
            else:
                alienInfoRequest = common.copy()
                alienInfoRequest.update({
                    'iqamaNumber': partner.identification_no,
                    'dateOfBirth': birth_date,
                })
                res = client.service.getAlienInfoByIqama(alienInfoRequest)
                return helpers.serialize_object(res, dict)
        except Fault as ex:
            raise UserError(_(ex))
        except Exception as ex:
            raise UserError(_('Elm & Yakeen API failed\n{}').format(ex))


class elm_yakeen_log(models.Model):
    _name = 'elm.yakeen.log'  # Defining model name
    _description = 'Elm Yakeen Log'  # Defining model description
    _order = "id desc"  # Setting default order by ID descending

    request = fields.Char(readonly=True)  # Request field, readonly
    response = fields.Char(readonly=True)  # Response field, readonly
    partner_id = fields.Many2one('res.partner', readonly=True)  # Many2one relation to 'res.partner', readonly
    api_method = fields.Char('API Method', readonly=True)  # API method field, readonly
