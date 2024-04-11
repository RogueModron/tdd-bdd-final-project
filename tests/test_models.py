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

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory


DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_a_product(self):
        """It should Read a product"""
        product = ProductFactory()
        app.logger.debug("Product to be created: %s", product.serialize())
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        #
        retrieved_product = Product.find(product.id)
        self.assertIsNotNone(retrieved_product)
        self.assertEqual(retrieved_product.id, product.id)
        self.assertEqual(retrieved_product.name, product.name)
        self.assertEqual(retrieved_product.description, product.description)
        self.assertEqual(Decimal(retrieved_product.price), product.price)
        self.assertEqual(retrieved_product.available, product.available)
        self.assertEqual(retrieved_product.category, product.category)

    def test_update_a_product(self):
        """It should Update a product"""
        product = ProductFactory()
        app.logger.debug("Product to be created: %s", product.serialize())
        product.id = None
        product.create()
        app.logger.debug("Product just created: %s", product.serialize())
        self.assertIsNotNone(product.id)
        #
        product.description = "This is the new description"
        product.update()
        #
        products = Product.all()
        self.assertEqual(len(products), 1)
        retrieved_product = products[0]
        self.assertEqual(retrieved_product.id, product.id)
        self.assertEqual(retrieved_product.name, product.name)
        self.assertEqual(retrieved_product.description, product.description)
        self.assertEqual(Decimal(retrieved_product.price), product.price)
        self.assertEqual(retrieved_product.available, product.available)
        self.assertEqual(retrieved_product.category, product.category)

    def test_delete_a_product(self):
        """It should Delete a product"""
        product_1 = ProductFactory()
        product_1.id = None
        product_1.create()
        product_2 = ProductFactory()
        product_2.id = None
        product_2.create()
        products = Product.all()
        self.assertEqual(len(products), 2)
        #
        product_1.delete()
        products = Product.all()
        self.assertEqual(len(products), 1)
        last_product = products[0]
        self.assertEqual(last_product.id, product_2.id)

    def test_list_all_products(self):
        """It should List all products"""
        products = Product.all()
        self.assertEqual(len(products), 0)
        #
        num_of_products = 5
        for _ in range(num_of_products):
            product = ProductFactory()
            product.id = None
            product.create()
        products = Product.all()
        self.assertEqual(len(products), num_of_products)

    def test_find_a_product_by_name(self):
        """It should Find a product by name"""
        created_products = []
        num_of_products = 5
        for _ in range(num_of_products):
            product = ProductFactory()
            product.id = None
            product.create()
            created_products.append(product)
        first_name = created_products[0].name
        num_with_first_name = sum(map(lambda p: p.name == first_name, created_products))
        app.logger.debug("Expected products: %i", num_with_first_name)
        #
        query = Product.find_by_name(first_name)
        products = query.all()
        self.assertEqual(len(products), num_with_first_name)
        for product in products:
            self.assertEqual(product.name, first_name)

    def test_find_a_product_by_availability(self):
        """It should Find a product by availability"""
        created_products = []
        num_of_products = 10
        for _ in range(num_of_products):
            product = ProductFactory()
            product.id = None
            product.create()
            created_products.append(product)
        first_availability = created_products[0].available
        num_with_first_availability = sum(map(lambda p: p.available == first_availability, created_products))
        app.logger.debug("Expected products: %i", num_with_first_availability)
        #
        query = Product.find_by_availability(first_availability)
        products = query.all()
        self.assertEqual(len(products), num_with_first_availability)
        for product in products:
            self.assertEqual(product.available, first_availability)

    def test_find_a_product_by_category(self):
        """It should Find a product by category"""
        created_products = []
        num_of_products = 10
        for _ in range(num_of_products):
            product = ProductFactory()
            product.id = None
            product.create()
            created_products.append(product)
        first_category = created_products[0].category
        num_with_first_category = sum(map(lambda p: p.category == first_category, created_products))
        app.logger.debug("Expected products: %i", num_with_first_category)
        #
        query = Product.find_by_category(first_category)
        products = query.all()
        self.assertEqual(len(products), num_with_first_category)
        for product in products:
            self.assertEqual(product.category, first_category)

    def test_find_a_product_by_price(self):
        """It should Find a product by price"""
        created_products = []
        num_of_products = 10
        for _ in range(num_of_products):
            product = ProductFactory()
            product.id = None
            product.create()
            created_products.append(product)
        first_price = created_products[0].price
        num_with_first_price = sum(map(lambda p: p.price == first_price, created_products))
        app.logger.debug("Expected products: %i", num_with_first_price)
        #
        query = Product.find_by_price(first_price)
        products = query.all()
        self.assertEqual(len(products), num_with_first_price)
        for product in products:
            self.assertEqual(product.price, first_price)

    def test_update_a_product_without_id(self):
        """It should Raise an exception when updating a product without id"""
        product = ProductFactory()
        product.id = None
        self.assertRaises(DataValidationError, product.update)

    def test_deserialize_a_product(self):
        """It should Deserialize a product"""
        product = ProductFactory()
        serialization = product.serialize()
        other_product = ProductFactory()
        other_product.deserialize(serialization)
        self.assertEqual(other_product.name, product.name)
        self.assertEqual(other_product.description, product.description)
        self.assertEqual(Decimal(other_product.price), product.price)
        self.assertEqual(other_product.available, product.available)
        self.assertEqual(other_product.category, product.category)

    def test_deserialize_a_product_with_invalid_availability(self):
        """It should Raise an exception when deserializing a product with invalid availability"""
        product = ProductFactory()
        serialization = product.serialize()
        serialization["available"] = "NoWay"
        self.assertRaises(DataValidationError, product.deserialize, serialization)

    def test_deserialize_a_product_with_invalid_attribute(self):
        """It should Raise an exception when deserializing a product with invalid attribute"""
        product = ProductFactory()
        serialization = product.serialize()
        serialization["category"] = "NoWay"
        self.assertRaises(DataValidationError, product.deserialize, serialization)

    def test_deserialize_a_product_with_a_missing_key(self):
        """It should Raise an exception when deserializing a product with a missing key"""
        product = ProductFactory()
        serialization = product.serialize()
        del serialization["name"]
        self.assertRaises(DataValidationError, product.deserialize, serialization)

    def test_deserialize_a_product_with_empty_data(self):
        """It should Raise an exception when deserializing a product with empty data"""
        product = ProductFactory()
        self.assertRaises(DataValidationError, product.deserialize, "")

    def test_find_a_product_by_price_with_a_string_value(self):
        """It should Find a product by price with a string value"""
        created_products = []
        num_of_products = 10
        for _ in range(num_of_products):
            product = ProductFactory()
            product.id = None
            product.create()
            created_products.append(product)
        first_price = created_products[0].price
        num_with_first_price = sum(map(lambda p: p.price == first_price, created_products))
        app.logger.debug("Expected products: %i", num_with_first_price)
        #
        query = Product.find_by_price(str(first_price))
        products = query.all()
        self.assertEqual(len(products), num_with_first_price)
        for product in products:
            self.assertEqual(product.price, first_price)
