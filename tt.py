import typer

app = typer.Typer(name="testing")

com = typer.Typer(name="com")


@app.command()
def foo():
    print("FOO!")


app.add_typer(com)

if __name__ == "__main__":
    app()
