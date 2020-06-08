from zac.accounts.permissions import Permission

zaken_inzien = Permission(
    name="zaken:inzien", description="Laat toe om zaken/zaakdossiers in te zien.",
)

zaakproces_usertasks = Permission(
    name="zaakproces:usertasks-uitvoeren",
    description="Usertasks claimen en/of uitvoeren als onderdeel van het zaakproces.",
)

zaakproces_send_message = Permission(
    name="zaakproces:send-bpmn-message",
    description="BPMN messages versturen in het proces.",
)

zaken_set_status = Permission(
    name="zaken:create-status", description="Zetten nieuwe statussen op zaken."
)

zaken_close = Permission(
    name="zaken:afsluiten",
    description="Zaken afsluiten (=eindstatus zetten), als er een resultaat gezet is.",
)

zaken_set_result = Permission(
    name="zaken:set-result", description="Resultaat zetten op zaken."
)

zaken_download_documents = Permission(
    name="zaken:download-documents",
    description="Inzien documenten bij zaken, inclusief de (binaire) inhoud.",
)