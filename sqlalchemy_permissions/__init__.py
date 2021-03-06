from functools import wraps
from werkzeug.exceptions import Forbidden


class Permissions(object):
    def __init__(self, user_class, role_class, user_getter=None):
        self.__user_class = user_class
        self.__role_class = role_class

        self.user_getter = user_getter

    def get_user(self):
        if self.user_getter:
            return self.user_getter()
        else:
            try:
                from flask.ext.login import current_user
                return current_user
            except ImportError:
                raise ImportError("User argument not passed and Flask-Login current_user could not be imported.")

    def user_has(self, desired_ability, owner_id=None):
        """
        Takes an ability (a string name of either a role or an ability) and returns the function if the user has that ability
        """

        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                current_user = self.get_user()

                if current_user:
                    if current_user.has_ability(desired_ability):
                        return func(*args, **kwargs)

                    ability_prefix, ability_suffix = desired_ability.rsplit(".", 1)
                    try:
                        object_id = int(ability_suffix)
                    except ValueError:
                        pass
                    else:
                        if object_id and current_user.id == owner_id and current_user.has_ability(ability_prefix + ".self"):
                            return func(*args, **kwargs)

                raise Forbidden()

            return inner

        return wrapper

    def user_is(self, role):
        """
        Take a role and returns the function if the user has that role
        Raise a Forbidden exception otherwise
        """

        def wrapper(func):
            @wraps(func)
            def inner(*args, **kwargs):
                desired_role = self.__role_class.query.filter_by(name=role).first()
                current_user = self.get_user()
                if current_user and current_user.has_role(desired_role):
                    return func(*args, **kwargs)
                raise Forbidden()

            return inner

        return wrapper

    def check_user_has(self, desired_ability, owner_id=None):
        # FIXME Ugly
        self.user_has(desired_ability, owner_id)(lambda: None)()
