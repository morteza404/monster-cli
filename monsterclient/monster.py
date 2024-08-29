import click
from monsterclient.api import MonsterAPI, AuthAPI, TokenV1, TokenV3

monsterAPI = MonsterAPI()
authAPI = AuthAPI()


@click.command(help="Change Project ID")
@click.argument("id", required=False)
def project(id):
    try:
        if id:
            response = authAPI.change_project_id(id)
            click.echo(f"{response.repr()}")
        else:
            monster_conn = authAPI.read_from_monster_connection_file()
            monster_url = monster_conn["monster"]
            splited_url = monster_url.split("/")
            auth_index = [
                i for i, word in enumerate(splited_url) if word.startswith("AUTH")
            ][0]
            response = splited_url[auth_index]
            click.echo(f"{response}")
    except Exception as e:
        handle_exception(e)


@click.command(help="GET a new token")
@click.option("-c", "--curl", is_flag=True, help="Prints cURL equivalent if specified")
@click.option("-v", "--version", help="Auth version")
def token(curl, version):
    try:
        if version == "3":
            token = TokenV3()
        elif version == "1" or version == None:
            token = TokenV1()

        response = authAPI.set_new_monster_connection(token)
        click.echo(f"{response.repr(curl=curl)}")
    except Exception as e:
        handle_exception(e)


@click.command(help="HEAD Account | Container | Object")
@click.argument("container", required=False)
@click.argument("obj", required=False)
@click.option(
    "-H",
    "--header",
    help="You can add headers to your request using this option",
)
@click.option("-c", "--curl", is_flag=True, help="Prints cURL equivalent if specified")
def head(container, obj, header, curl):
    try:
        if obj and container:
            response = monsterAPI.head_object(container, obj, header)
        elif not obj and container:
            response = monsterAPI.head_container(container, header)
        else:
            response = monsterAPI.head_account(header)

        click.echo(f"{response.repr(curl=curl)}")
    except Exception as e:
        handle_exception(e)


@click.command(help="GET Account | Container | Object")
@click.argument("container", required=False)
@click.argument("obj", required=False)
@click.option(
    "-H",
    "--header",
    help="You can add headers to your request using this option",
)
@click.option("-c", "--curl", is_flag=True, help="Prints cURL equivalent if specified")
def get(container, obj, header, curl):
    try:
        if obj and container:
            response = monsterAPI.get_object(container, obj, header)
        elif not obj and container:
            response = monsterAPI.get_container(container, header)
        else:
            response = monsterAPI.get_account(header)

        click.echo(f"{response.repr(curl=curl)}")
    except Exception as e:
        handle_exception(e)


@click.command(help="PUT Container | Object")
@click.argument("container")
@click.argument("obj", required=False)
@click.option(
    "-H",
    "--header",
    help="To set metadata use: X-{Container|Object}-Meta-Key: Value",
)
@click.option("-c", "--curl", is_flag=True, help="Prints cURL equivalent if specified")
def put(container, obj, header, curl):
    try:
        if obj:
            response = monsterAPI.upload_object(container, obj, header)
        else:
            response = monsterAPI.create_container(container, header)

        click.echo(f"{response.repr(curl=curl)}")
    except Exception as e:
        handle_exception(e)


@click.command(help="POST Account | Container | Object")
@click.argument("container", required=False)
@click.argument("obj", required=False)
@click.option(
    "-H",
    "--header",
    help="To set metadata use: X-{Account|Container|Object}-Meta-Key: Value",
)
@click.option("-c", "--curl", is_flag=True, help="Prints cURL equivalent if specified")
def post(container, obj, header, curl):
    try:
        if obj and container:
            response = monsterAPI.post_object(container, obj, header)
        elif not obj and container:
            response = monsterAPI.post_container(container, header)
        else:
            response = monsterAPI.post_account(header)

        click.echo(f"{response.repr(curl=curl)}")
    except Exception as e:
        handle_exception(e)


@click.command(help="DELETE Container | Object")
@click.argument("container")
@click.argument("obj", required=False)
@click.option(
    "-H",
    "--header",
    help="You can add headers to your request using this option",
)
@click.option("-c", "--curl", is_flag=True, help="Prints cURL equivalent if specified")
def delete(container, header, obj, curl):
    try:
        if obj:
            response = monsterAPI.delete_object(container, obj, header)
        else:
            response = monsterAPI.delete_container(container, header)

        click.echo(f"{response.repr(curl=curl)}")
    except Exception as e:
        handle_exception(e)


@click.command(help="Get info")
@click.option("-c", "--curl", is_flag=True, help="Prints cURL equivalent if specified")
def info(curl):
    try:
        response = monsterAPI.get_info()
        click.echo(f"{response.repr(curl=curl)}")
    except Exception as e:
        handle_exception(e)


@click.group(help="CLI tool for Monster")
def main():
    pass


main.add_command(project)
main.add_command(token)
main.add_command(head)
main.add_command(get)
main.add_command(put)
main.add_command(post)
main.add_command(delete)
main.add_command(info)


def handle_exception(e):
    click.echo("Sorry, something is wrong \U0001F641")
    click.echo("You may want to try the followings:")
    click.echo("\U0001F449 Get token via monster token")
    click.echo("\U0001F449 Check your env variables to see if they are correctly set.")
    click.echo("\U0001F449 Check your connection by monster info")
    click.echo("\U0001F449 Maybe you are issuing a wrong command?")
    click.echo()
    click.echo(f"Error: {str(e)}")
    click.echo()
    main("--help")


if __name__ == "__main__":
    main()
