######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
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
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_routes.py:TestProductRoutes
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_get_product(self):
        """It should Get a Product"""
        test_product = self._create_products()[0]
        response = self.client.get(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_product = response.get_json()
        self.assertEqual(retrieved_product["name"], test_product.name)
        self.assertEqual(retrieved_product["description"], test_product.description)
        self.assertEqual(Decimal(retrieved_product["price"]), test_product.price)
        self.assertEqual(retrieved_product["available"], test_product.available)
        self.assertEqual(retrieved_product["category"], test_product.category.name)

    def test_get_product_not_found(self):
        """It should not Get a Product"""
        response = self.client.get(BASE_URL + "/666")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product(self):
        """It should Update a Product"""
        test_product = self._create_products()[0]
        test_product.description = "This is the new description and you can't deny it"
        response = self.client.put(BASE_URL + "/" + str(test_product.id), json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_product = response.get_json()
        self.assertEqual(retrieved_product["description"], test_product.description)

    def test_update_product_not_found(self):
        """It should not Update a Product"""
        test_product = ProductFactory()
        serialized = test_product.serialize()
        response = self.client.put(BASE_URL + "/666", json=serialized)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product(self):
        """It should Delete a Product"""
        test_product = self._create_products()[0]
        response = self.client.get(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_product = response.get_json()
        self.assertEqual(retrieved_product["name"], test_product.name)
        response = self.client.delete(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.get(BASE_URL + "/" + str(test_product.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product_not_found(self):
        """It should not Delete a Product"""
        response = self.client.delete(BASE_URL + "/666")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_all_products(self):
        """It should List all Products"""
        num_of_products = 3
        self._create_products(num_of_products)
        product_count = self.get_product_count()
        self.assertEqual(product_count, num_of_products)

    def test_list_products_by_name(self):
        """It should List Products by name"""
        num_of_products = 10
        test_products = self._create_products(num_of_products)
        first_name = test_products[0].name
        num_with_first_name = sum(map(lambda p: p.name == first_name, test_products))
        response = self.client.get(BASE_URL + "?name=" + first_name)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_products = response.get_json()
        self.assertEqual(len(retrieved_products), num_with_first_name)
        for product in retrieved_products:
            self.assertEqual(product["name"], first_name)

    def test_list_products_by_category(self):
        """It should List Products by category"""
        num_of_products = 10
        test_products = self._create_products(num_of_products)
        first_category = test_products[0].category
        num_with_first_category = sum(map(lambda p: p.category == first_category, test_products))
        response = self.client.get(BASE_URL + "?category=" + first_category.name)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_products = response.get_json()
        self.assertEqual(len(retrieved_products), num_with_first_category)
        for product in retrieved_products:
            self.assertEqual(product["category"], first_category.name)

    def test_list_products_by_availability(self):
        """It should List Products by availability"""
        num_of_products = 10
        test_products = self._create_products(num_of_products)
        first_available = test_products[0].available
        num_with_first_available = sum(map(lambda p: p.available == first_available, test_products))
        response = self.client.get(BASE_URL + "?available=" + str(first_available))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        retrieved_products = response.get_json()
        self.assertEqual(len(retrieved_products), num_with_first_available)
        for product in retrieved_products:
            self.assertEqual(product["available"], first_available)

    def test_list_products_with_more_then_one_query_parameter(self):
        """It should not List Products when more than one query parameter is used"""
        response = self.client.get(BASE_URL + "?name=hello&availability=false")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_products_with_unknown_query_parameter(self):
        """It should not List Products when an unknown query parameter is used"""
        response = self.client.get(BASE_URL + "?goaway=no")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_products_with_not_existing_category(self):
        """It should not List Products when a category that does not exist is used"""
        response = self.client.get(BASE_URL + "?category=hacking-bs")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
