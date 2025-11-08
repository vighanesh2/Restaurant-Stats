MOCK_ORDER_DATA = {
    "external_user_id": "234638",
    "url": "https://www.doordash.com/orders/53d1a2e5-c037-4784-85ae-c2311c7de909",
    "orderStatus": "COMPLETED",
    "shipping": {
        "location": {
            "address": {
                "line1": "7799 William St",
                "city": "Princeton",
                "region": "NJ",
                "postalCode": "08540",
                "countryCode": "US",
            },
            "firstName": None,
            "lastName": None,
            "name": None,
            "rawValue": None,
            "emailAddress": None,
            "phoneNumber": None,
        },
        "arrivalDate": None,
    },
    "store": {
        "location": {
            "address": {
                "line1": "20 Witherspoon Street",
                "city": "Princeton",
                "region": "NJ",
                "postalCode": "08542",
                "countryCode": "US",
            },
            "phoneNumber": "+16094545936",
            "name": "Mamoun's Falafel - Princeton",
        }
    },
    "paymentMethods": [
        {
            "externalId": "7f74be92-d602-4e5b-8a9d-0cf2fa4a132e",
            "type": "CARD",
            "brand": "VISA",
            "last4": "1635",
            "transactionAmount": 77.13,
            "billing": {
                "location": {
                    "address": [],
                    "firstName": None,
                    "lastName": None,
                    "name": None,
                    "rawValue": None,
                    "emailAddress": None,
                    "phoneNumber": None,
                }
            },
        }
    ],
    "price": {
        "subTotal": 71.12,
        "adjustments": [
            {"type": "FEE", "label": "Delivery Fee", "amount": 0},
            {"type": "FEE", "label": "Service Fee", "amount": 3.56},
            {"type": "TAX", "label": "Estimated Tax", "amount": 4.45},
            {"type": "DISCOUNT", "label": "Discount", "amount": -4},
            {"type": "TIP", "label": "Dasher Tip", "amount": 2},
        ],
        "total": 77.13,
        "currency": "USD",
    },
    "products": [
        {
            "externalId": "32805316241",
            "name": "Seasoned Fries",
            "description": "Served with choice of garlic dipping sauce or ketchup",
            "url": None,
            "quantity": 4,
            "eligibility": None,
            "price": {
                "subTotal": 22.04,
                "total": 22.04,
                "unitPrice": 5.51,
            },
            "orderStatus": "COMPLETED",
            "imageUrl": "https://img.cdn4dd.com/cdn-cgi/image/fit=contain,width=1200,height=672,format=auto/https://doordash-static.s3.amazonaws.com/media/photosV2/b8e34b04-119a-4a64-a106-fb431c47bda5-retina-large.jpg",
        },
        {
            "externalId": "32805316224",
            "name": "Falafel Sandwich",
            "description": "Finely ground chickpeas, onions, parsley, garlic, and spices, deep fried; served in a pita pocket with lettuce, tomatoes, onions, and tahineh sauce",
            "url": None,
            "quantity": 2,
            "eligibility": None,
            "price": {
                "subTotal": 15.52,
                "total": 15.52,
                "unitPrice": 7.76,
            },
            "orderStatus": "COMPLETED",
            "imageUrl": "https://img.cdn4dd.com/cdn-cgi/image/fit=contain,width=1200,height=672,format=auto/https://doordash-static.s3.amazonaws.com/media/photosV2/a505c501-0a3a-4d8e-acb5-251a0d2964c5-retina-large.jpg",
        },
        {
            "externalId": "32805316238",
            "name": "Chicken Kebob Plate",
            "description": "Marinated cubes of chicken breast, skewered and grilled; served over choice of salad or seasoned rice (or both for additional charge) and tahineh sauce, with a pita bread on the side",
            "url": None,
            "quantity": 2,
            "eligibility": None,
            "price": {
                "subTotal": 33.56,
                "total": 33.56,
                "unitPrice": 16.78,
            },
            "orderStatus": "COMPLETED",
            "imageUrl": "https://img.cdn4dd.com/cdn-cgi/image/fit=contain,width=1200,height=672,format=auto/https://doordash-static.s3.amazonaws.com/media/photosV2/c7006297-446d-4672-8cb3-1f3f4aeb487c-retina-large.jpg",
        },
    ],
    "schema_version": "11/07/2024",
    "raw": '{"externalId":"53d1a2e5-c037-4784-85ae-c2311c7de909","dateTime":"1762564241134","url":"https://www.doordash.com/orders/53d1a2e5-c037-4784-85ae-c2311c7de909","orderStatus":"COMPLETED","isKnotCard":false,"shipping":{"location":{"address":{"line1":"7799 William St","city":"Princeton","region":"NJ","postalCode":"08540","countryCode":"US"}}},"store":{"location":{"address":{"line1":"20 Witherspoon Street","city":"Princeton","region":"NJ","postalCode":"08542","countryCode":"US"},"name":"Mamoun\'s Falafel - Princeton","phoneNumber":"+16094545936"}},"paymentMethods":[{"externalId":"7f74be92-d602-4e5b-8a9d-0cf2fa4a132e","type":"CARD","brand":"VISA","lastFour":"1635","transactionAmount":77.13}],"price":{"subTotal":71.12,"adjustments":[{"type":"FEE","label":"Delivery Fee","amount":0},{"type":"FEE","label":"Service Fee","amount":3.56},{"type":"TAX","label":"Estimated Tax","amount":4.45},{"type":"DISCOUNT","label":"Discount","amount":-4},{"type":"TIP","label":"Dasher Tip","amount":2}],"total":77.13},"products":[{"externalId":"32805316241","name":"Seasoned Fries","description":"Served with choice of garlic dipping sauce or ketchup","quantity":4,"price":{"subTotal":22.04,"total":22.04,"unitPrice":5.51},"orderStatus":"COMPLETED","imageUrl":"https://img.cdn4dd.com/cdn-cgi/image/fit=contain,width=1200,height=672,format=auto/https://doordash-static.s3.amazonaws.com/media/photosV2/b8e34b04-119a-4a64-a106-fb431c47bda5-retina-large.jpg"},{"externalId":"32805316224","name":"Falafel Sandwich","description":"Finely ground chickpeas, onions, parsley, garlic, and spices, deep fried; served in a pita pocket with lettuce, tomatoes, onions, and tahineh sauce","quantity":2,"price":{"subTotal":15.52,"total":15.52,"unitPrice":7.76},"orderStatus":"COMPLETED","imageUrl":"https://img.cdn4dd.com/cdn-cgi/image/fit=contain,width=1200,height=672,format=auto/https://doordash-static.s3.amazonaws.com/media/photosV2/a505c501-0a3a-4d8e-acb5-251a0d2964c5-retina-large.jpg"},{"externalId":"32805316238","name":"Chicken Kebob Plate","description":"Marinated cubes of chicken breast, skewered and grilled; served over choice of salad or seasoned rice (or both for addt\\u2019l charge) and tahineh sauce, with a pita bread on the side","quantity":2,"price":{"subTotal":33.56,"total":33.56,"unitPrice":16.78},"orderStatus":"COMPLETED","imageUrl":"https://img.cdn4dd.com/cdn-cgi/image/fit=contain,width=1200,height=672,format=auto/https://doordash-static.s3.amazonaws.com/media/photosV2/c7006297-446d-4672-8cb3-1f3f4aeb487c-retina-large.jpg"}}]}',
    "task": {"merchant_id": 19, "id": 2821854, "attempt": 1},
    "raw_type": "json",
    "accuracy": None,
    "accuracy_checks": [],
}

