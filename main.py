import discord.app_commands
import discord
import json
import asyncio
import distutils


intents = discord.Intents.default()  # 標準設定から
intents.typing = False  # typingは受け取らない
intents.message_content = True  # message_contentは受け取る
intents.members = True

guild = discord.Object(1082464517025431692)

client = discord.Client(intents=intents)
TOKEN = "MTA4MjU4ODI1MzU1Njg0NjYzMg.GDsGMV.4Da4uPra3tMqC2O-QCt4c7ITQlpYxtPdGoA6Wk"
tree = discord.app_commands.CommandTree(client)

######### 設定用のクラス設定 ##########
class RoleSelectViewForSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="ロールを選択してください"
    )
    async def roleselectMenu(self, ctx: discord.Interaction, roleselect: discord.ui.RoleSelect):
        with open('FanBoxManager/data.json', 'r') as f:
            json_dict = json.load(f)
        json_dict[str(ctx.guild_id)]["roles"] = {}
        rolelist = []
        for role in roleselect.values:
            json_dict[str(ctx.guild_id)]["roles"][role.name] = role.id
            rolelist.append('**'+role.name+'**')
        roleselect.disabled = True
        await ctx.response.edit_message(view=self)
        embed = discord.Embed(color = 0x00ff00, title= "設定完了", description="以下のロールを付与できるようになりました。\n" + '\n'.join(rolelist))
        await ctx.followup.send(embed=embed,ephemeral=True)
        with open("FanBoxManager/data.json", "w") as f:
            json.dump(json_dict, f, ensure_ascii=False)

class AutoRoleSelectViewForSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        placeholder="ロールを選択してください"
    )
    async def roleselectMenu(self, ctx: discord.Interaction, roleselect: discord.ui.RoleSelect):
        with open('FanBoxManager/data.json', 'r') as f:
            json_dict = json.load(f)
        json_dict[str(ctx.guild_id)]["autoroles"] = {}
        rolelist = []
        for role in roleselect.values:
            json_dict[str(ctx.guild_id)]["autoroles"][role.name] = role.id
            rolelist.append('**'+role.name+'**')
        roleselect.disabled = True
        await ctx.response.edit_message(view=self)
        embed = discord.Embed(color = 0x00ff00, title= "設定完了", description="以下のロールを自動で付与します。\n" + '\n'.join(rolelist))
        await ctx.followup.send(embed=embed,ephemeral=True)
        with open("FanBoxManager/data.json", "w") as f:
            json.dump(json_dict, f, ensure_ascii=False)

class ChannelSelectViewForReceiveSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="チャンネルを選択してください"
    )
    async def receivechannelselectMenu(self, ctx: discord.Interaction, channelselect: discord.ui.ChannelSelect):
        with open('FanBoxManager/data.json', 'r') as f:
            json_dict = json.load(f)
        json_dict[str(ctx.guild_id)
                  ]["receive_channel"] = channelselect.values[0].id
        await ctx.response.send_message("設定しました。", delete_after=5)
        await ctx.guild.get_channel(channelselect.values[0].id).send("画像送信用チャンネルに設定されました。", delete_after=5)
        with open("FanBoxManager/data.json", "w") as f:
            json.dump(json_dict, f, ensure_ascii=False)
        await asyncio.sleep(5)
        await ctx.followup.delete_message(ctx.message.id)

class ChannelSelectViewForBotSetting(discord.ui.View):
    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        placeholder="チャンネルを選択してください"
    )
    async def botchannelselectMenu(self, ctx: discord.Interaction, channelselect: discord.ui.ChannelSelect):
        with open('FanBoxManager/data.json', 'r') as f:
            json_dict = json.load(f)
        json_dict[str(ctx.guild_id)]["bot_channel"] = channelselect.values[0].id
        await ctx.response.send_message("設定しました。", delete_after=5)
        await ctx.guild.get_channel(channelselect.values[0].id).send("画像確認用チャンネルに設定されました。", delete_after=5)
        with open("FanBoxManager/data.json", "w") as f:
            json.dump(json_dict, f, ensure_ascii=False)
        await asyncio.sleep(5)
        await ctx.followup.delete_message(ctx.message.id)

class my_Button_for_role_granting(discord.ui.Button):
    def __init__(self, *, style: discord.ButtonStyle = discord.ButtonStyle.secondary, label: str, role_id: int, user_id: int):
        super().__init__(style=style, label=label)
        self.role_id = role_id
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        print("Buttoncallback")
        if self.role_id == -1:
            await interaction.message.delete()
            return
        member = interaction.guild.get_member(self.user_id)
        role = interaction.guild.get_role(self.role_id)
        await member.add_roles(role)
        await interaction.response.send_message(f"{role.name}を付与しました", ephemeral=True, delete_after=5)

        #embed = discord.Embed(color = 0x00ff00, title = "ロール付与のお知らせ",description=f"お待たせしました。\n**{role.name}**が付与されました。")
        # embed.set_author(name="FanBoxManager")
        # await interaction.guild.send(embed = embed)

        #embed = discord.Embed(color = 0x00ff00, title = "ロール付与のお知らせ",description=f"**{interaction.guild.name}**にて**{role.name}**が付与されました。")
        # embed.set_author(name="FanBoxManager")
        # await member.send(embed = embed)
        
class my_Button_for_role_auto_grant(discord.ui.Button):
    def __init__(self, *, style: discord.ButtonStyle = discord.ButtonStyle.secondary, label: str, isroleautogranted: str):
        super().__init__(style=style, label=label)
        self.isroleautogranted = isroleautogranted

    async def callback(self, interaction: discord.Interaction):
        print("Buttoncallback")
        with open('FanBoxManager/data.json', 'r') as f:
            json_dict = json.load(f)
        json_dict[str(interaction.guild_id)]["isroleautogranted"] = self.isroleautogranted
        await interaction.response.send_message("設定しました", ephemeral=True, delete_after=5)
        await interaction.followup.delete_message(interaction.message.id)
        with open("FanBoxManager/data.json", "w") as f:
            json.dump(json_dict, f, ensure_ascii=False)
        
####################################


@tree.command(
    name="setting_role",  # コマンド名
    description="付与ロールに関する設定を行います。",  # コマンドの説明
    guild=guild
)
async def setting_role(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません",ephemeral = True)
        return
    roleview = RoleSelectViewForSetting(timeout=None)
    roleview.roleselectMenu.max_values = len(ctx.guild.roles)
    embed1 = discord.Embed(title="設定できるロールの選択")
    await ctx.response.send_message(view=roleview, embed=embed1, ephemeral=True)

@tree.command(
    name="setting_automatic_granting_role",  # コマンド名
    description="どのロールを自動付与するかを指定します。",  # コマンドの説明
    guild=guild
)
async def setting_auto_role(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません",ephemeral = True)
        return
    roleview = AutoRoleSelectViewForSetting(timeout=None)
    roleview.roleselectMenu.max_values = len(ctx.guild.roles)
    embed1 = discord.Embed(title="自動付与されるロールの選択")
    await ctx.response.send_message(view=roleview, embed=embed1, ephemeral=True)

@tree.command(
    name="setting_receive_channel",  # コマンド名
    description="画像を受信するチャンネルに関する設定を行います。",  # コマンドの説明
    guild=guild
)
async def setting_receive_channel(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません",ephemeral = True)
        return
    channelview = ChannelSelectViewForReceiveSetting(timeout=None)
    embed1 = discord.Embed(title="画像送信用チャンネルの選択")
    await ctx.response.send_message(view=channelview, embed=embed1, ephemeral=True)

@tree.command(
    name="setting_bot_channel",  # コマンド名
    description="画像を確認するチャンネルに関する設定を行います。",  # コマンドの説明
    guild=guild
)
async def setting_bot_channel(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません",ephemeral = True)
        return
    channelview = ChannelSelectViewForBotSetting(timeout=None)
    embed1 = discord.Embed(title="画像確認用チャンネルの選択")
    await ctx.response.send_message(view=channelview, embed=embed1, ephemeral=True)

@tree.command(
    name="setting_automatic_granting",  # コマンド名
    description="ロールを自動付与するかどうかを設定します。",  # コマンドの説明
    guild=guild
)
async def setting_receive_channel(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません",ephemeral = True)
        return
    view = discord.ui.View(timeout=None)
    view.add_item(my_Button_for_role_auto_grant(style=discord.ButtonStyle.primary,label="ON",isroleautogranted="True"))
    view.add_item(my_Button_for_role_auto_grant(style=discord.ButtonStyle.red,label="OFF",isroleautogranted="False"))
    embed1 = discord.Embed(title="ロールの自動付与のONOFF")
    await ctx.response.send_message(view=view, embed=embed1, ephemeral=True)

@tree.command(
    name="preset",  # コマンド名
    description="設定を初期化します。",  # コマンドの説明
    guild=guild
)
async def preset(ctx: discord.Interaction):
    if not ctx.user.guild_permissions.administrator:
        await ctx.response.send_message(f"実行する権限がありません",ephemeral = True)
        return
    print("preset")
    with open('FanBoxManager/data.json', 'r') as f:
        json_dict = json.load(f)

    json_dict[str(ctx.guild_id)] = {"admin": ctx.user.id, "bot_channel": 0, "receive_channel": 0, "roles": {
    }, "isroleautogranted": "False", "autoroles": {}}

    if ctx.guild.get_channel(json_dict[str(ctx.guild_id)]["bot_channel"]) is None:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
        }
        bot_channel = await ctx.guild.create_text_channel(name="確認チャンネル", overwrites=overwrites)
        json_dict[str(ctx.guild_id)]["bot_channel"] = bot_channel.id

    if ctx.guild.get_channel(json_dict[str(ctx.guild_id)]["receive_channel"]) is None:
        receive_channel = await ctx.guild.create_text_channel(name="権限付与チャンネル")
        json_dict[str(ctx.guild_id)]["receive_channel"] = receive_channel.id

    with open("FanBoxManager/data.json", "w") as f:
        json.dump(json_dict, f, ensure_ascii=False)

    embed = discord.Embed(color=0x00ff00, title="初期設定完了",
                          description="初期設定が完了しました。\n以下の設定コマンドを並行して使ってください。")
    embed.add_field(name="\\setting_roles", value="付与できるロールの設定をします。", inline=False)
    embed.add_field(name="\\setting_bot_channel",
                    value="送信した画像を確認し、ロールを付与するチャンネルを変更できます。", 
                    inline=False)
    embed.add_field(name="\\setting_receive_channel",
                    value="画像を送信してもらうチャンネルを変更できます。", 
                    inline=False)
    await ctx.response.send_message(embed=embed, ephemeral=True)


@client.event  # 画像送信部分をこちらで代用
async def on_message(message):
    print("message")
    with open('FanBoxManager/data.json', 'r') as f:
        json_dict = json.load(f)
    if message.author.bot:
        return
    if message.channel.id == json_dict[str(message.guild.id)]["receive_channel"]:
        if len(message.attachments) == 1:
            print("画像認識")
            if distutils.util.strtobool(json_dict[str(message.guild.id)]["isroleautogranted"]):
                for roleid in json_dict[str(message.guild.id)]["autoroles"].values():
                    await message.author.add_roles(message.guild.get_role(roleid))
                await message.add_reaction('\N{THUMBS UP SIGN}')
            else:
                image = await message.attachments[0].to_file(filename="image.png")
                bot_channel = message.guild.get_channel(
                    json_dict[str(message.guild.id)]["bot_channel"])
                embed = discord.Embed(
                    title="支援情報", description=f"{message.author.name}さんの支援情報です。", color=0xff0000)
                embed.set_author(name="FanBoxManager")
                embed.set_image(url=f"attachment://image.png")
                components = discord.ui.View(timeout=None)
                for rolename, roleid in json_dict[str(message.guild.id)]["roles"].items():
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
    guild=guild
)
async def claimrole(ctx:discord.Interaction, attachment: discord.Attachment):
    image = await attachment.to_file(filename="image.png")
    with open('FanBoxManager/data.json', 'r') as f:
        json_dict = json.load(f)
        await ctx.response.defer(ephemeral=True)
        bot_channel = await ctx.guild.fetch_channel(json_dict[str(ctx.guild_id)]["bot_channel"])
        embed = discord.Embed(title="支援情報",description=f"{ctx.user.name}さんの支援情報です。",color=0xff0000)
        embed.set_author(name="FanBoxManager")
        embed.set_image(url=f"attachment://image.png")
        components = discord.ui.View()
        components.add_item(item = my_Button(style = discord.ButtonStyle.gray, label = "付与終了", role_id=-1,user_id=-1))
        for rolename, roleid in json_dict[str(ctx.guild_id)]["roles"].items():
            components.add_item(item = my_Button(style = discord.ButtonStyle.primary, label = f"{rolename}", role_id=roleid, user_id = ctx.user.id))
        await bot_channel.send(file = image, embed = embed, view = components)
    await ctx.followup.send("受け取りました。\nロール付与まで少々お待ちください。",ephemeral=True)
'''





@client.event
# clientの準備完了時に呼び出されるイベント
async def on_ready():
    print("ready")
    await tree.sync(guild=guild)
    # await tree.sync()
    print('ready')

client.run(TOKEN)
