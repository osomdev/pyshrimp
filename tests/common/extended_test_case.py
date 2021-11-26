from typing import Dict
from unittest import TestCase


class ExtendedTestCase(TestCase):

    def assertDictContainsElements(self, expected_elements: Dict, actual: Dict, message: str = 'Dict does not contain expected elements'):
        self.assertIsInstance(actual, dict)

        errors = []

        for k, v in expected_elements.items():
            if k not in actual:
                errors.append(f'!! The element "{k}" is missing. Expected to be: "{v}"')

            elif actual[k] != v:
                actual_v = actual[k]
                errors.append(
                    f'!! Unexpected value of "{k}": "{v}" != "{actual_v}"\n'
                    f'\n'
                    f'Expected :{v}\n'
                    f'Actual   :{actual_v}\n'
                )

        if errors:
            errors_formatted = "\n".join(errors)
            self.fail(
                f'{message}\n'
                f'Assertion errors:\n'
                f'{errors_formatted}\n'
                f'Actual dict: {actual}\n'
            )
