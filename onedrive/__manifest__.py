# -*- coding: utf-8 -*-
{
    "name": "OneDrive / SharePoint Odoo Integration",
    "version": "15.0.1.1.5",
    "category": "Document Management",
    "author": "faOtools",
    "website": "https://faotools.com/apps/15.0/onedrive-sharepoint-odoo-integration-643",
    "license": "Other proprietary",
    "application": True,
    "installable": True,
    "auto_install": False,
    "depends": [
        "cloud_base"
    ],
    "data": [
        "data/data.xml",
        "security/ir.model.access.csv",
        "views/clouds_client.xml"
    ],
    "assets": {},
    "demo": [
        
    ],
    "external_dependencies": {
        "python": [
                "microsoftgraph-python",
                "requests"
        ]
},
    "summary": "The tool to automatically synchronize Odoo attachments with OneDrive files in both ways",
    "description": """For the full details look at static/description/index.html
* Features * 
- How synchronization works
#odootools_proprietary""",
    "images": [
        "static/description/main.png"
    ],
    "price": "134.0",
    "currency": "EUR",
    "live_test_url": "https://faotools.com/my/tickets/newticket?&url_app_id=44&ticket_version=15.0&url_type_id=3",
}