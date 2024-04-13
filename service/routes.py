######################################################################
# Copyright 2016, 2022 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

# spell: ignore Rofrano jsonify restx dbname
"""
Product Store Service with UI
"""
from flask import jsonify, request, abort
from flask import url_for  # noqa: F401 pylint: disable=unused-import
from service.models import Product, Category
from service.common import status  # HTTP Status Codes
from . import app


######################################################################
# H E A L T H   C H E C K
######################################################################
@app.route("/health")
def healthcheck():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="OK"), status.HTTP_200_OK


######################################################################
# H O M E   P A G E
######################################################################
@app.route("/")
def index():
    """Base URL for our service"""
    return app.send_static_file("index.html")


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################
def check_content_type(content_type):
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# C R E A T E   A   N E W   P R O D U C T
######################################################################
@app.route("/products", methods=["POST"])
def create_products():
    """
    Creates a Product
    This endpoint will create a Product based the data in the body that is posted
    """
    app.logger.info("Request to Create a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)
    product = Product()
    product.deserialize(data)
    product.create()
    app.logger.info("Product with new id [%s] saved!", product.id)

    message = product.serialize()

    #
    # Uncomment this line of code once you implement READ A PRODUCT
    #
    location_url = url_for("get_products", product_id=product.id, _external=True)
    # location_url = "/"  # delete once READ is implemented
    return jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# L I S T   A L L   P R O D U C T S
######################################################################
@app.route("/products")
def list_all_products():
    """
        Get a list of products
        TODO:
    """
    if len(request.args) > 1:
        abort(
            status.HTTP_400_BAD_REQUEST
        )

    param = ""
    value = ""
    if len(request.args) == 1:
        (param, value) = next(iter(request.args.items()))
        param = param.lower()

    if param not in ["", "name", "category", "available"]:
        abort(
            status.HTTP_400_BAD_REQUEST
        )

    if param == "name":
        products = Product.find_by_name(value)
    elif param == "category":
        category = Category.UNKNOWN
        try:
            category = getattr(Category, value)
        except AttributeError:
            abort(
                status.HTTP_400_BAD_REQUEST
            )
        products = Product.find_by_category(category)
    elif param == "available":
        available = value.lower() == "true"
        products = Product.find_by_availability(available)
    else:
        products = Product.all()
    serialized_products = []
    for product in products:
        serialized_products.append(product.serialize())
    return jsonify(serialized_products), status.HTTP_200_OK


######################################################################
# R E A D   A   P R O D U C T
######################################################################
@app.route("/products/<product_id>")
def get_products(product_id):
    """
        Read a product
        TODO:
    """
    product = Product.find(product_id)
    if product is None:
        abort(
            status.HTTP_404_NOT_FOUND
        )
    return jsonify(product.serialize()), status.HTTP_200_OK


######################################################################
# U P D A T E   A   P R O D U C T
######################################################################
@app.route("/products/<product_id>", methods=["PUT"])
def update_products(product_id):
    """
    Updates a Product
    This endpoint will update a Product based the data in the body
    """
    app.logger.info("Request to Update a Product...")
    check_content_type("application/json")

    data = request.get_json()
    app.logger.info("Processing: %s", data)

    product = Product.find(product_id)
    if product is None:
        abort(
            status.HTTP_404_NOT_FOUND
        )

    product.deserialize(data)
    product.update()
    app.logger.info("Product with id [%s] updated!", product.id)

    message = product.serialize()

    return jsonify(message), status.HTTP_200_OK


######################################################################
# D E L E T E   A   P R O D U C T
######################################################################
@app.route("/products/<product_id>", methods=["DELETE"])
def delete_products(product_id):
    """
    Delete a Product
    This endpoint will delete a Product
    """
    app.logger.info("Request to Delete a Product...")

    app.logger.info("Processing: %s", product_id)

    product = Product.find(product_id)
    if product is None:
        abort(
            status.HTTP_404_NOT_FOUND
        )

    product.delete()
    app.logger.info("Product with id [%s] deleted!", product.id)

    return "", status.HTTP_204_NO_CONTENT
