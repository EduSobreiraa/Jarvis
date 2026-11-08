var app = Application.currentApplication()
app.includeStandardAdditions = true

function run() {
  try {
    app.doShellScript("/bin/zsh '/Users/eduardopires/projetos/Jarvis/scripts/start-jarvis.sh'")
  } catch (error) {
    app.displayDialog(
      "Não consegui iniciar o Jarvis. Veja os registros em data/logs dentro da pasta do projeto.\n\n" + error,
      { buttons: ["OK"], defaultButton: "OK", withIcon: "stop" }
    )
  }
}
