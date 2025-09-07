from django.db import models


class AccountEmailaddress(models.Model):
    email = models.CharField(unique=True, max_length=254)
    verified = models.BooleanField()
    primary = models.BooleanField()
    user = models.ForeignKey('AuthUser', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailaddress'
        unique_together = (('user', 'email'), ('user', 'primary'),)


class AccountEmailconfirmation(models.Model):
    created = models.DateTimeField()
    sent = models.DateTimeField(blank=True, null=True)
    key = models.CharField(unique=True, max_length=64)
    email_address = models.ForeignKey(AccountEmailaddress, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'account_emailconfirmation'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoFlatpage(models.Model):
    url = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    content = models.TextField()
    enable_comments = models.BooleanField()
    template_name = models.CharField(max_length=70)
    registration_required = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'django_flatpage'


class DjangoFlatpageSites(models.Model):
    id = models.BigAutoField(primary_key=True)
    flatpage = models.ForeignKey(DjangoFlatpage, models.DO_NOTHING)
    site = models.ForeignKey('DjangoSite', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_flatpage_sites'
        unique_together = (('flatpage', 'site'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjangoSite(models.Model):
    domain = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'django_site'


class GameCategories(models.Model):
    name = models.CharField(unique=True, max_length=100)
    slug = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = 'game_categories'


class GameCategoryAssociation(models.Model):
    game = models.ForeignKey('SteamGames', models.DO_NOTHING)
    category = models.ForeignKey(GameCategories, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'game_category_association'
        unique_together = (('game', 'category'),)


class GamePriceHistory(models.Model):
    app_id = models.IntegerField()
    game = models.ForeignKey('SteamGames', models.DO_NOTHING, blank=True, null=True)
    current_price = models.CharField(max_length=50)
    original_price = models.CharField(max_length=50)
    discount_percent = models.IntegerField()
    recorded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'game_price_history'


class SocialaccountSocialaccount(models.Model):
    provider = models.CharField(max_length=200)
    uid = models.CharField(max_length=191)
    last_login = models.DateTimeField()
    date_joined = models.DateTimeField()
    extra_data = models.JSONField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialaccount'
        unique_together = (('provider', 'uid'),)


class SocialaccountSocialapp(models.Model):
    provider = models.CharField(max_length=30)
    name = models.CharField(max_length=40)
    client_id = models.CharField(max_length=191)
    secret = models.CharField(max_length=191)
    key = models.CharField(max_length=191)
    provider_id = models.CharField(max_length=200)
    settings = models.JSONField()

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp'


class SocialaccountSocialappSites(models.Model):
    id = models.BigAutoField(primary_key=True)
    socialapp = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING)
    site = models.ForeignKey(DjangoSite, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialapp_sites'
        unique_together = (('socialapp', 'site'),)


class SocialaccountSocialtoken(models.Model):
    token = models.TextField()
    token_secret = models.TextField()
    expires_at = models.DateTimeField(blank=True, null=True)
    account = models.ForeignKey(SocialaccountSocialaccount, models.DO_NOTHING)
    app = models.ForeignKey(SocialaccountSocialapp, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'socialaccount_socialtoken'
        unique_together = (('app', 'account'),)


class SteamGames(models.Model):
    app_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    clean_title = models.CharField(max_length=255)
    current_price = models.CharField(max_length=50)
    original_price = models.CharField(max_length=50)
    discount_percent = models.IntegerField()
    discount_amount = models.CharField(max_length=50, blank=True, null=True)
    url = models.CharField(unique=True, max_length=500)
    image_url = models.TextField(blank=True, null=True)
    capsule_image = models.TextField(blank=True, null=True)
    review_rating = models.CharField(max_length=100, blank=True, null=True)
    review_count = models.CharField(max_length=100, blank=True, null=True)
    positive_reviews = models.IntegerField(blank=True, null=True)
    total_reviews = models.IntegerField(blank=True, null=True)
    review_score = models.IntegerField(blank=True, null=True)
    categories = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    genres = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    release_date = models.CharField(max_length=100, blank=True, null=True)
    developer = models.CharField(max_length=200, blank=True, null=True)
    publisher = models.CharField(max_length=200, blank=True, null=True)
    min_requirements = models.TextField(blank=True, null=True)
    rec_requirements = models.TextField(blank=True, null=True)
    is_free = models.BooleanField(blank=True, null=True)
    is_discounted = models.BooleanField(blank=True, null=True)
    is_early_access = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    last_checked = models.DateTimeField(blank=True, null=True)
    discount_start = models.DateTimeField(blank=True, null=True)
    discount_end = models.DateTimeField(blank=True, null=True)
    steam_rating = models.CharField(max_length=50, blank=True, null=True)
    metacritic_score = models.IntegerField(blank=True, null=True)
    supported_languages = models.TextField(blank=True, null=True)
    platforms = models.TextField(blank=True, null=True)
    features = models.TextField(blank=True, null=True)
    popularity_score = models.FloatField(blank=True, null=True)
    weight = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'steam_games'
