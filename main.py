import discord
import json
import asyncio
import os
import sys
import typing
import mysql.connector

intents = discord.Intents.default()  # 標準設定から
intents.typing = False  # typingは受け取らない
intents.message_content = True  # message_contentは受け取る
intents.members = True


############################################
# 対応するMySQLの表の一覧
# guild_id(bigint), admin_id(bigint), bot_channel_id(bigint), receive_channel_id(bigint), roles_id(json), autorole(ENUM("True","False")), autoroles_id(json)
############################################

######### 設定用のクラス設定 ##########
class RoleSelectViewForSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="ロールを選択してください"
    )
    async def roleselectMenu(self, ctx: discord.Interaction, roleselect: discord.ui.RoleSelect):
        dict = mysql_to_dict_by_guild_id(cursor, str(ctx.guild_id))
        dict["roles_id"] = {}
        rolelist = []
        for role in roleselect.values:
            dict["roles_id"][role.name] = role.id
            rolelist.append('**'+role.name+'**')
        roleselect.disabled = True
        await ctx.response.edit_message(view=self)
        embed = discord.Embed(color=0x00ff00, title="設定完了",
                              description="以下のロールを付与できるようになりました。\n" + '\n'.join(rolelist))
        await ctx.followup.send(embed=embed, ephemeral=True)
        dict_to_mysql(cursor, dict)


class AutoRoleSelectViewForSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="ロールを選択してください"
    )
    async def roleselectMenu(self, ctx: discord.Interaction, roleselect: discord.ui.RoleSelect):
        dict = mysql_to_dict_by_guild_id(cursor, str(ctx.guild_id))
        dict["autoroles_id"] = {}
        rolelist = []
        for role in roleselect.values:
            dict["autoroles_id"][role.name] = role.id
            rolelist.append('**'+role.name+'**')
        roleselect.disabled = True
        await ctx.response.edit_message(view=self)
        embed = discord.Embed(color=0x00ff00, title="設定完了",
                              description="以下のロールを自動で付与します。\n" + '\n'.join(rolelist))
        await ctx.followup.send(embed=embed, ephemeral=True)
        dict_to_mysql(cursor, dict)


class ChannelSelectViewForReceiveSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="チャンネルを選択してください"
    )
    async def receivechannelselectMenu(self, ctx: discord.Interaction, channelselect: discord.ui.ChannelSelect):
        dict = mysql_to_dict_by_guild_id(cursor, str(ctx.guild_id))
        dict["receive_channel_id"] = channelselect.values[0].id
        await ctx.response.send_message("設定しました。", delete_after=5)
        await ctx.guild.get_channel(channelselect.values[0].id).send("画像送信用チャンネルに設定されました。", delete_after=5)
        dict_to_mysql(cursor, dict)
        await asyncio.sleep(5)
        await ctx.followup.delete_message(ctx.message.id)


class ChannelSelectViewForBotSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="チャンネルを選択してください"
    )
    async def botchannelselectMenu(self, ctx: discord.Interaction, channelselect: discord.ui.ChannelSelect):
        dict = mysql_to_dict_by_guild_id(cursor, str(ctx.guild_id))
        dict["bot_channel_id"] = channelselect.values[0].id
        await ctx.response.send_message("設定しました。", delete_after=5)
        await ctx.guild.get_channel(channelselect.values[0].id).send("画像確認用チャンネルに設定されました。", delete_after=5)
        dict_to_mysql(cursor, dict)
        await asyncio.sleep(5)
        await ctx.followup.delete_message(ctx.message.id)


class my_Button_for_role_granting(discord.ui.Button):
    def __init__(self, *, style: discord.ButtonStyle = discord.ButtonStyle.secondary, label: str, role_id: int, user_id: int):
        super().__init__(style=style, label=label)
        self.role_id = role_id
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        sys.stdout.write("Buttoncallback")
        if self.role_id == -1:
            await interaction.message.delete()
            return
        member = interaction.guild.get_member(self.user_id)
        role = interaction.guild.get_role(self.role_id)
        await member.add_roles(role)
        await interaction.response.send_message(f"{role.name}を付与しました", ephemeral=True, delete_after=5)

        # embed = discord.Embed(color = 0x00ff00, title = "ロール付与のお知らせ",description=f"お待たせしました。\n**{role.name}**が付与されました。")
        # embed.set_author(name="FanBoxManager")
        # await interaction.guild.send(embed = embed)

        # embed = discord.Embed(color = 0x00ff00, title = "ロール付与のお知らせ",description=f"**{interaction.guild.name}**にて**{role.name}**が付与されました。")
        # embed.set_author(name="FanBoxManager")
        # await member.send(embed = embed)


class my_Button_for_role_auto_grant(discord.ui.Button):
    def __init__(self, *, style: discord.ButtonStyle = discord.ButtonStyle.secondary, label: str, isroleautogranted: str):
        super().__init__(style=style, label=label)
        self.isroleautogranted = isroleautogranted

    async def callback(self, interaction: discord.Interaction):
        sys.stdout.write("Buttoncallback")
        dict = mysql_to_dict_by_guild_id(cursor, str(interaction.guild_id))
        dict["autorole"] = self.isroleautogranted
        await interaction.response.send_message("設定しました", ephemeral=True, delete_after=5)
        await interaction.followup.delete_message(interaction.message.id)
        dict_to_mysql(cursor, dict)

####################################

########## Mysql-dict間関数 ##########


def mysql_to_dict_by_guild_id(cursor: mysql.connector.cursor.MySQLCursor, guild_id: int):
    cursor.execute("show columns from guilddata")
    dict = {}

    columns = [column[0] for column in cursor]

    for column in columns:
        cursor.execute(
            f"select {column} from guilddata WHERE guild_id = {guild_id}")

        for item in cursor:
            if isinstance(item[0], int):
                dict[str(column)] = item[0]
            elif isinstance(item[0], str):
                if item[0][0] == '{':
                    dict[str(column)] = json.loads(item[0])
                else:
                    dict[str(column)] = item[0]
    return dict


def dict_to_mysql(cursor: mysql.connector.cursor.MySQLCursor, dict: dict):
    for key in dict.keys():
        if isinstance(dict[key],typing.Dict):
            dict[key] = json.dumps(dict[key])
    query_value = ', '.join(map(lambda s: str(s) if isinstance(s, int) else '\'' + str(s) + '\'', dict.values())).rstrip(',')
    key_value = ', '.join(dict.keys()).rstrip(',')
    update_value = ','.join(map(lambda key, value: str(key) + '=' + str(value) if isinstance(value, int) else str(key) + '=\'' + str(value) + '\'', dict.keys(),dict.values())).rstrip(',')
    try:
        query = f"INSERT INTO guilddata ({key_value}) VALUES ({query_value}) ON DUPLICATE KEY UPDATE {update_value}"
        print(query)
        cursor.execute(query)
        cnx.commit()
    except Exception as e:
        cnx.rollback()
        raise e

#####################################

client = discord.Client(intents=intents)
MYSQLUSER = os.environ.get("MYSQLUSER")
MYSQLPASSWORD = os.environ.get("MYSQLPASSWORD")
MYSQLHOST = os.environ.get("MYSQLHOST")
MYSQLDATABASE = os.environ.get("MYSQLDATABASE")
MYSQLPORT = os.environ.get("MYSQLPORT")
TOKEN = os.environ.get("DISCORD_TOKEN")
tree = discord.app_commands.CommandTree(client)
cnx = None
cursor = None

try:
    cnx = mysql.connector.connect(
        user=MYSQLUSER,  # ユーザー名
        password=MYSQLPASSWORD,  # パスワード
        host=MYSQLHOST,  # ホスト名(IPアドレス）
        database=MYSQLDATABASE,  # データベース
        port = MYSQLPORT,
        auth_plugin='mysql_native_password'
    )

    if cnx.is_connected:
        print("Connected!")

    cursor = cnx.cursor()

except Exception as e:
    print(f"Error Occurred: {e}")


@tree.command(
    name="setting_role",  # コマンド名
    description="付与ロールに関する設定を行います。",  # コマンドの説明
    
)
async def setting_role(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません", ephemeral=True)
        return
    roleview = RoleSelectViewForSetting(timeout=None)
    roleview.roleselectMenu.max_values = len(ctx.guild.roles)
    embed1 = discord.Embed(title="設定できるロールの選択")
    await ctx.response.send_message(view=roleview, embed=embed1, ephemeral=True)


@tree.command(
    name="setting_automatic_granting_role",  # コマンド名
    description="どのロールを自動付与するかを指定します。",  # コマンドの説明
    
)
async def setting_auto_role(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません", ephemeral=True)
        return
    roleview = AutoRoleSelectViewForSetting(timeout=None)
    roleview.roleselectMenu.max_values = len(ctx.guild.roles)
    embed1 = discord.Embed(title="自動付与されるロールの選択")
    await ctx.response.send_message(view=roleview, embed=embed1, ephemeral=True)


@tree.command(
    name="setting_receive_channel",  # コマンド名
    description="画像を受信するチャンネルに関する設定を行います。",  # コマンドの説明
    
)
async def setting_receive_channel(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません", ephemeral=True)
        return
    channelview = ChannelSelectViewForReceiveSetting(timeout=None)
    embed1 = discord.Embed(title="画像送信用チャンネルの選択")
    await ctx.response.send_message(view=channelview, embed=embed1, ephemeral=True)


@tree.command(
    name="setting_bot_channel",  # コマンド名
    description="画像を確認するチャンネルに関する設定を行います。",  # コマンドの説明
    
)
async def setting_bot_channel(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません", ephemeral=True)
        return
    channelview = ChannelSelectViewForBotSetting(timeout=None)
    embed1 = discord.Embed(title="画像確認用チャンネルの選択")
    await ctx.response.send_message(view=channelview, embed=embed1, ephemeral=True)


@tree.command(
    name="setting_automatic_granting",  # コマンド名
    description="ロールを自動付与するかどうかを設定します。",  # コマンドの説明
    
)
async def setting_receive_channel(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません", ephemeral=True)
        return
    view = discord.ui.View(timeout=None)
    view.add_item(my_Button_for_role_auto_grant(
        style=discord.ButtonStyle.primary, label="ON", isroleautogranted="True"))
    view.add_item(my_Button_for_role_auto_grant(
        style=discord.ButtonStyle.red, label="OFF", isroleautogranted="False"))
    embed1 = discord.Embed(title="ロールの自動付与のONOFF")
    await ctx.response.send_message(view=view, embed=embed1, ephemeral=True)

@tree.command(
    name="setting_preview",  # コマンド名
    description="現在の設定を確認します。",  # コマンドの説明
    
)
async def setting_preview(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません", ephemeral=True)
        return
    dict = mysql_to_dict_by_guild_id(cursor, str(ctx.guild_id))
    bot_channel = ctx.guild.get_channel(dict["bot_channel_id"])
    receive_channel = ctx.guild.get_channel(dict["receive_channel_id"])
    roles = dict["roles_id"].keys()
    autorole = "有効" if dict["autorole"] == "True" else "無効"
    autoroles = dict["autoroles_id"].keys()
    embed = discord.Embed(color=0x00ff00, title="設定の一覧", description="このサーバーにおける現在の設定です。")
    embed.add_field(name="画像検知チャンネル",value=receive_channel.name,inline=False)
    embed.add_field(name="認証チャンネル",value=bot_channel.name,inline=False)
    embed.add_field(name="付与できるロール一覧",value=",".join(roles),inline=False)
    embed.add_field(name="ロールの自動付与",value=autorole,inline=False)
    embed.add_field(name="自動付与されるロール一覧",value=",".join(autoroles),inline=False)
    await ctx.response.send_message(embed=embed, ephemeral=True)


@tree.command(
    name="preset",  # コマンド名
    description="設定を初期化します。",  # コマンドの説明
    
)
async def preset(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません", ephemeral=True)
        return
    sys.stdout.write("preset")

    dict = {"admin_id": ctx.user.id, "guild_id": ctx.guild_id, "bot_channel_id": 0,
            "receive_channel_id": 0, "roles_id": {}, "autorole": "False", "autoroles_id": "{}"}

    if ctx.guild.get_channel(dict["bot_channel_id"]) is None:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        bot_channel = await ctx.guild.create_text_channel(name="確認チャンネル", overwrites=overwrites)
        dict["bot_channel_id"] = bot_channel.id

    if ctx.guild.get_channel(dict["receive_channel_id"]) is None:
        receive_channel = await ctx.guild.create_text_channel(name="権限付与チャンネル")
        dict["receive_channel_id"] = receive_channel.id

    dict_to_mysql(cursor, dict)

    embed = discord.Embed(color=0x00ff00, title="初期設定完了",
                          description="初期設定が完了しました。\n以下の設定コマンドを並行して使ってください。")
    embed.add_field(name="\\setting_roles",
                    value="付与できるロールの設定をします。", inline=False)
    embed.add_field(name="\\setting_bot_channel",
                    value="送信した画像を確認し、ロールを付与するチャンネルを変更できます。",
                    inline=False)
    embed.add_field(name="\\setting_receive_channel",
                    value="画像を送信してもらうチャンネルを変更できます。",
                    inline=False)
    await ctx.response.send_message(embed=embed, ephemeral=True)


@client.event  # 画像送信部分をこちらで代用
async def on_message(message):
    if message.author.bot:
        return
    dict = mysql_to_dict_by_guild_id(cursor,message.guild.id)
    if message.channel.id == dict["receive_channel_id"]:
        if len(message.attachments) == 1:
            sys.stdout.write("画像認識")
            if dict["autorole"] == "True":
                for roleid in dict["autoroles_id"].values():
                    await message.author.add_roles(message.guild.get_role(roleid))
                await message.add_reaction('\N{THUMBS UP SIGN}')
            else:
                image = await message.attachments[0].to_file(filename="image.png")
                bot_channel = message.guild.get_channel(dict["bot_channel_id"])
                embed = discord.Embed(
                    title="支援情報", description=f"{message.author.name}さんの支援情報です。", color=0xff0000)
                embed.set_author(name="FanBoxManager")
                embed.set_image(url=f"attachment://image.png")
                components = discord.ui.View(timeout=None)
                for rolename, roleid in dict["roles_id"].items():
                    components.add_item(item=my_Button_for_role_granting(
                        style=discord.ButtonStyle.primary, label=f"{rolename}", role_id=roleid, user_id=message.author.id))
                components.add_item(item=my_Button_for_role_granting(
                    style=discord.ButtonStyle.gray, label="付与終了", role_id=-1, user_id=-1))
                await bot_channel.send(file=image, embed=embed, view=components)
                await message.add_reaction('\N{THUMBS UP SIGN}')


'''
@tree.command(
    name="claimrole",#コマンド名
    description="支援情報を送信することでロールの付与を申請します。",#コマンドの説明
    
)
async def claimrole(ctx:discord.Interaction, attachment: discord.Attachment):
    image = await attachment.to_file(filename="image.png")
    with open('data.json', 'r') as f:
        dict = json.load(f)
        await ctx.response.defer(ephemeral=True)
        bot_channel = await ctx.guild.fetch_channel(dict["bot_channel_id"])
        embed = discord.Embed(title="支援情報",description=f"{ctx.user.name}さんの支援情報です。",color=0xff0000)
        embed.set_author(name="FanBoxManager")
        embed.set_image(url=f"attachment://image.png")
        components = discord.ui.View()
        components.add_item(item = my_Button(style = discord.ButtonStyle.gray, label = "付与終了", role_id=-1,user_id=-1))
        for rolename, roleid in dict["roles"].items():
            components.add_item(item = my_Button(style = discord.ButtonStyle.primary, label = f"{rolename}", role_id=roleid, user_id = ctx.user.id))
        await bot_channel.send(file = image, embed = embed, view = components)
    await ctx.followup.send("受け取りました。\nロール付与まで少々お待ちください。",ephemeral=True)
'''


@client.event
# clientの準備完了時に呼び出されるイベント
async def on_ready():
    sys.stdout.write("ready")
    await tree.sync()
    # await tree.sync()
    sys.stdout.write('ready')
client.run(TOKEN)
