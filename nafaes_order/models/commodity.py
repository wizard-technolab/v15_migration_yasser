from odoo import api, fields, models, _  # Import necessary classes and functions from Odoo


class NafaesCommodity(models.Model):
    _name = "nafaes.commodity"  # Define the model name
    _inherit = "nafaes.api.mixin"  # Inherit from nafaes.api.mixin
    _description = "Nafaes Commodity"  # Set the model description
    _rec_name = 'name'  # Set the display name for records

    name = fields.Char()  # Define a Char field for the commodity name

    def action_refresh_commodities(self):
        """Fetches and updates the list of available commodities from the API."""

        response = self.nafaes_get_available_commodities()  # Fetch the available commodities from the API
        if response['status'] == 'success':  # Check if the API response is successful
            for item in response['response']:  # Iterate over each item in the response
                values = {
                    'commodityCode': item['commodityCode'],  # Set the commodity code
                    'commodityName': item['commodityName'],  # Set the commodity name
                    'commoditySource': item['commoditySource'],  # Set the commodity source
                    'commoditySourceId': item['commoditySourceId'],  # Set the commodity source ID
                }
                existing_id = self.search(
                    [('commodityCode', '=', values['commodityCode'])])  # Search for existing commodity by code
                if existing_id:
                    existing_id.write(values)  # Update the existing commodity
                else:
                    self.create(values)  # Create a new commodity record
