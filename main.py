from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.uix.screenmanager import Screen, ScreenManager, NoTransition
from kivy.uix.relativelayout import RelativeLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivy.properties import StringProperty
from kivymd.uix.tab import MDTabsBase
from kivy.core.window import Window

CATEGORIES = ["Pasta", "Breakfast", "Seafood", "Dessert", "Vegetarian", "Starter"]

# Window.size = (1080/2, 2082/2)

Builder.load_file("recipe_app.kv")


class Tab(MDFloatLayout, MDTabsBase):
    """Class implementing content for a tab."""


class HomeScreen(Screen):
    pass


class SearchResultsScreen(Screen):
    pass


class CategoriesScreen(Screen):
    app = None

    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.current_category = ""
        for category in CATEGORIES:
            self.ids.category_tabs.add_widget(Tab(title=category))

    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        """
        Called when switching tabs.

        :type instance_tabs: <kivymd.uix.tab.MDTabs object>;
        :param instance_tab: <__main__.Tab object>;
        :param instance_tab_label: <kivymd.uix.tab.MDTabsLabel object>;
        :param tab_text: text or name icon of tab;
        """
        self.current_category = tab_text
        self.ids.categories_results_grid.clear_widgets()
        self.ids.categories_results_grid.add_widget(CenteredSpinner())
        self.ids.categories_results_grid.height = (
            self.ids.categories_results_grid.minimum_height
        )
        self.ids.categories_results_label.text = f"Loading recipes for {tab_text}..."

        UrlRequest(
            f"https://www.themealdb.com/api/json/v1/1/filter.php?c={tab_text.replace(' ', '%20')}",
            self.show_category_results,
            verify=False,
        )

    def view_category(self, category_title):
        self.ids.category_tabs.switch_tab(
            search_by="property title", name_tab=category_title
        )

    def show_category_results(self, req, result):
        category_results = result["meals"]

        self.ids.categories_results_grid.clear_widgets()
        self.ids.categories_results_label.text = f'{len(category_results)} search result{"s" if len(category_results) > 1 else ""} for "{self.current_category}"'

        for category_result in category_results:
            self.ids.categories_results_grid.add_widget(
                RecipeMedium(
                    source=category_result["strMealThumb"],
                    title=f"[size={int(self.app.scale(11))}][color=#ffffff][b] {category_result['strMeal']}[/b][/color][/size]",
                    category=f"[size=10][color=#808080][b]{self.current_category}[/b][/color][/size]",
                    recipe_id=category_result["idMeal"],
                    from_screen="categories",
                )
            )

        num_results_row = len(category_results) / 2
        if len(category_result) == 1:
            num_results_row = 1
        if num_results_row % 2 == 1:
            num_results_row += 0.5
        self.ids.categories_results_grid.height = self.app.scale(num_results_row * 170)

class RandomRecipeScreen(Screen):
    title = StringProperty("")
    img = StringProperty("")
    recipe_id = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.title = kw["title"]
        self.img = kw["img"]
        self.recipe_id = kw["recipe_id"]


class LoadingScreen(Screen):
    pass


class NoResults(RelativeLayout):
    pass


class CenteredSpinner(RelativeLayout):
    pass


class RecipeMedium(RelativeLayout):
    source = StringProperty("")
    title = StringProperty("")
    category = StringProperty("")
    recipe_id = StringProperty("")
    from_screen = StringProperty("")


class RecipeStep(RelativeLayout):
    text = StringProperty("")


class RecipeIngredient(RelativeLayout):
    img = StringProperty("")
    title = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)


class RecipeDetailScreen(Screen):
    title = StringProperty("")
    img = StringProperty("")
    category = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        self.title = kw["title"]
        self.img = kw["img"]
        self.category = kw["category"]


class RecipeApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.back_screen = "home"
        self.search_value = ""
        self.window_width = Window.size[0]
        self.window_height = Window.size[1]
        self.scale_by = (self.window_width * self.window_height)/520000
        self.scale_by += 0.35

    def scale(self, value):
        return value * 2.5

    def update_layout_height(self):
        recipe_details_container = self.recipe_detail.ids.recipe_steps
        recipe_details_container.height = self.recipe_step.ids.label.texture_size[1]

    def load_random_recipe(self):
        UrlRequest(
            "https://www.themealdb.com/api/json/v1/1/random.php",
            self.show_random_recipe,
            verify=False,
        )

        self.sm.current = "loading"

    def show_random_recipe(self, req, result):
        data = result["meals"][0]
        self.random_recipe.title = data["strMeal"]
        self.random_recipe.img = data["strMealThumb"]
        self.random_recipe.recipe_id = data["idMeal"]

        self.sm.current = "random_recipe"

    def load_recipe_detail(self, recipe_id, from_screen):
        self.back_screen = from_screen
        UrlRequest(
            f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}",
            self.show_recipe_detail,
            verify=False,
        )

        self.sm.current = "loading"

    def show_recipe_detail(self, req, result):
        data = result["meals"][0]
        self.sm.remove_widget(self.recipe_detail)
        self.recipe_detail = RecipeDetailScreen(
            name="recipe_detail", title="", img="", category=""
        )
        self.sm.add_widget(self.recipe_detail)

        self.recipe_detail.title = data["strMeal"]
        self.recipe_detail.img = data["strMealThumb"]
        self.recipe_detail.category = data["strCategory"]

        instructions = data["strInstructions"]

        if "\n\n" not in instructions:
            instructions = instructions.replace("\n", "\n\n")

        recipe_details_container = self.recipe_detail.ids.recipe_steps

        self.recipe_step = RecipeStep(text=instructions)
        recipe_details_container.add_widget(self.recipe_step)

        recipe_ingredients_container = self.recipe_detail.ids.recipe_ingredients

        for i in range(20):
            i += 1
            title = f"{data['strMeasure'+str(i)]} {data['strIngredient'+str(i)]}"
            if (
                title.strip() == ""
                or data["strMeasure" + str(i)] is None
                or data["strIngredient" + str(i)] is None
            ):
                break

            img = f"https://www.themealdb.com/images/ingredients/{data['strIngredient'+str(i)].replace(' ', '%20')}.png"

            recipe_ingredients_container.add_widget(
                RecipeIngredient(img=img, title=title)
            )

        self.sm.current = "recipe_detail"

    def recipe_detail_back(self):
        self.sm.current = self.back_screen

    def load_search_results(self, root):
        self.search_value = root.ids.search_bar.text
        UrlRequest(
            f"https://www.themealdb.com/api/json/v1/1/search.php?s={self.search_value.replace(' ', '%20')}",
            self.show_search_results,
            verify=False,
        )
        self.sm.current = "loading"

    def show_search_results(self, req, result):
        search_results = result["meals"]
        self.sm.remove_widget(self.search_results)
        self.search_results = SearchResultsScreen(name="search_results")
        self.sm.add_widget(self.search_results)

        self.search_results.ids.search_bar.text = self.search_value
        self.search_results.ids.search_results_grid.clear_widgets()

        if search_results is None:
            self.search_results.ids.search_results_label.text = ""
            self.search_results.ids.search_results_container.add_widget(NoResults())
            self.sm.current = "search_results"
            self.search_results.ids.search_results_container.height = (
                self.search_results.ids.search_results_container.minimum_height
            )
            return

        for search_result in search_results:
            self.search_results.ids.search_results_grid.add_widget(
                RecipeMedium(
                    source=search_result["strMealThumb"],
                    title=f"[size={int(self.scale(11))}][color=#ffffff][b] {search_result['strMeal']}[/b][/color][/size]",
                    category=f"[size=10][color=#808080][b]{search_result['strCategory']}[/b][/color][/size]",
                    recipe_id=search_result["idMeal"],
                    from_screen="search_results",
                )
            )
        num_results_row = len(search_results) / 2
        if len(search_results) == 1:
            num_results_row = 1
        if num_results_row % 2 == 1:
            num_results_row += 0.5
        self.search_results.ids.search_results_grid.height = self.scale(
            num_results_row * 170
        )
        self.search_results.ids.search_results_label.text = f'{len(search_results)} search result{"s" if len(search_results) > 1 else ""} for "{self.search_value}"'
        self.sm.current = "search_results"

    def view_category(self, category_title):
        self.sm.current = "categories"
        self.categories_screen.view_category(category_title=category_title)

    def build(self):
        self.theme_cls.primary_palette = "Brown"
        self.sm = ScreenManager(transition=NoTransition())
        self.home = HomeScreen(name="home")
        self.sm.add_widget(self.home)
        self.random_recipe = RandomRecipeScreen(
            name="random_recipe", title="", img="", recipe_id=""
        )
        self.sm.add_widget(self.random_recipe)
        self.sm.add_widget(LoadingScreen(name="loading"))
        self.recipe_detail = RecipeDetailScreen(
            name="recipe_detail", title="", img="", category=""
        )
        self.sm.add_widget(self.recipe_detail)
        self.search_results = SearchResultsScreen(name="search_results")
        self.sm.add_widget(self.search_results)
        self.categories_screen = CategoriesScreen(self, name="categories")
        self.sm.add_widget(self.categories_screen)
        return self.sm


if __name__ == "__main__":
    RecipeApp().run()
