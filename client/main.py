"""Cliente GymVe (Flet) — login contra API FastAPI. APK Android vía `flet build apk`."""

import os

import flet as ft
import httpx

SPECIAL = set("!@#$%^&*()_+-=[]{}|;:',.<>?/`~\"\\")
DEFAULT_API = os.getenv("GYMVE_API_BASE_URL", "http://10.0.2.2:8000").rstrip("/")

VIOLET_DEEP = "#5B21B6"
ELECTRIC = "#2563EB"
PINK = "#EC4899"
LIME = "#C4F042"
SKY = "#38BDF8"
BG_DARK = "#120828"
TEXT = "#F8FAFC"
MUTED = "rgba(248,250,252,0.72)"
GLASS = "rgba(255,255,255,0.11)"

BTN_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.center_left,
    end=ft.alignment.center_right,
    colors=[LIME, SKY, PINK, "#A78BFA"],
)

PAGE_GRADIENT = ft.LinearGradient(
    begin=ft.alignment.top_left,
    end=ft.alignment.bottom_right,
    colors=[BG_DARK, VIOLET_DEEP, ELECTRIC, "#4C1D95"],
)


def policy_ok(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "La contraseña debe tener al menos 10 caracteres."
    if not any(c in SPECIAL for c in password):
        return False, "La contraseña debe incluir al menos un carácter especial."
    return True, ""


def field_style() -> dict:
    return {
        "bgcolor": "rgba(15,10,40,0.55)",
        "border_color": "rgba(255,255,255,0.22)",
        "focused_border_color": LIME,
        "color": TEXT,
        "label_style": ft.TextStyle(color=MUTED, size=12),
        "text_style": ft.TextStyle(color=TEXT, size=16),
        "border_radius": 12,
        "content_padding": ft.padding.symmetric(horizontal=16, vertical=14),
    }


def main(page: ft.Page) -> None:
    page.title = "GymVe"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(font_family="Roboto")
    page.bgcolor = BG_DARK

    api_field = ft.TextField(
        label="URL del servidor API",
        value=page.client_storage.get("gymve_api_base") or DEFAULT_API,
        hint_text="http://192.168.1.10:8000",
        autofocus=False,
        **field_style(),
    )
    email_field = ft.TextField(
        label="Correo electrónico",
        keyboard_type=ft.KeyboardType.EMAIL,
        autocorrect=False,
        **field_style(),
    )
    password_field = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
        **field_style(),
    )
    error_text = ft.Text("", color="#FCA5A5", size=13, visible=False)
    loading = ft.ProgressRing(visible=False, width=22, height=22, color=LIME)

    home_content = ft.Column(visible=False, spacing=12)
    login_card = ft.Column(spacing=12)

    def show_error(msg: str) -> None:
        error_text.value = msg
        error_text.visible = bool(msg)
        page.update()

    def go_home(profile: dict) -> None:
        login_card.visible = False
        home_content.visible = True
        home_content.controls.clear()
        home_content.controls.extend(
            [
                ft.Text("Bienvenido/a", size=12, color=MUTED),
                ft.Text(
                    profile.get("display_name", ""),
                    size=26,
                    weight=ft.FontWeight.W_600,
                    color=TEXT,
                ),
                ft.Text(profile.get("email", ""), size=14, color=MUTED),
                ft.Container(
                    bgcolor="rgba(255,255,255,0.1)",
                    border=ft.border.all(0.5, "rgba(196,240,66,0.35)"),
                    border_radius=12,
                    padding=16,
                    content=ft.Text(
                        "Sesión iniciada. Aquí irán rutinas y progreso de GymVe.",
                        size=13,
                        color=MUTED,
                    ),
                ),
                ft.OutlinedButton(
                    "Cerrar sesión",
                    on_click=logout_click,
                    style=ft.ButtonStyle(
                        color=TEXT,
                        side=ft.BorderSide(0.5, "rgba(255,255,255,0.28)"),
                    ),
                ),
            ]
        )
        page.update()

    def logout_click(_e: ft.ControlEvent) -> None:
        page.client_storage.remove("gymve_token")
        home_content.visible = False
        login_card.visible = True
        password_field.value = ""
        show_error("")
        page.update()

    async def submit_login(_e: ft.ControlEvent) -> None:
        show_error("")
        email = (email_field.value or "").strip()
        password = password_field.value or ""
        base = (api_field.value or DEFAULT_API).rstrip("/")

        if not email:
            show_error("Introduce tu correo.")
            return
        ok, msg = policy_ok(password)
        if not ok:
            show_error(msg)
            return

        loading.visible = True
        page.update()
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{base}/api/v1/login",
                    json={"email": email, "password": password},
                )
            if resp.status_code == 400:
                detail = resp.json().get("detail", "Contraseña no válida.")
                show_error(str(detail))
                return
            if resp.status_code == 401:
                show_error("Correo o contraseña incorrectos.")
                return
            if resp.status_code >= 400:
                show_error(f"Error del servidor ({resp.status_code}). Revisa la URL API.")
                return
            data = resp.json()
            page.client_storage.set("gymve_token", data["access_token"])
            page.client_storage.set("gymve_api_base", base)
            go_home(data)
        except httpx.RequestError:
            show_error(
                "No se pudo conectar al servidor. Comprueba Wi‑Fi, la URL API y que el backend esté en marcha."
            )
        finally:
            loading.visible = False
            page.update()

    logo = ft.Container(
        width=72,
        height=72,
        border_radius=36,
        gradient=BTN_GRADIENT,
        alignment=ft.alignment.center,
        content=ft.Text("GV", size=22, weight=ft.FontWeight.W_600, color=BG_DARK),
    )

    glass = lambda child: ft.Container(
        content=child,
        bgcolor=GLASS,
        border=ft.border.all(0.5, "rgba(255,255,255,0.28)"),
        border_radius=16,
        padding=ft.padding.symmetric(horizontal=22, vertical=24),
    )

    login_card.controls.extend(
        [
            ft.Row([logo], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text(
                "GymVe",
                size=32,
                weight=ft.FontWeight.W_600,
                text_align=ft.TextAlign.CENTER,
                color=TEXT,
            ),
            ft.Text(
                "Tu energía, tu ritmo, tu progreso",
                size=14,
                color=MUTED,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text("Fuerza", size=11, color=TEXT),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=20,
                        bgcolor="rgba(255,255,255,0.12)",
                        border=ft.border.all(0.5, "rgba(255,255,255,0.22)"),
                    ),
                    ft.Container(
                        content=ft.Text("Constancia", size=11, color=TEXT),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        border_radius=20,
                        bgcolor="rgba(255,255,255,0.12)",
                        border=ft.border.all(0.5, "rgba(255,255,255,0.22)"),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True,
            ),
            glass(
                ft.Column(
                    [
                        ft.Text("Acceso familiar", size=18, weight=ft.FontWeight.W_500, color=TEXT),
                        api_field,
                        email_field,
                        password_field,
                        ft.Text(
                            "Mín. 10 caracteres y un símbolo especial (!@#…).",
                            size=11,
                            color="rgba(248,250,252,0.55)",
                        ),
                        error_text,
                        ft.Row(
                            [
                                ft.Container(
                                    content=ft.Text(
                                        "Entrar",
                                        size=15,
                                        weight=ft.FontWeight.W_500,
                                        color=BG_DARK,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    gradient=BTN_GRADIENT,
                                    border_radius=12,
                                    padding=ft.padding.symmetric(vertical=14),
                                    expand=True,
                                    alignment=ft.alignment.center,
                                    on_click=submit_login,
                                    ink=True,
                                ),
                                loading,
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=12,
                )
            ),
        ]
    )

    page.add(
        ft.Container(
            expand=True,
            gradient=PAGE_GRADIENT,
            padding=24,
            content=ft.Column(
                [
                    login_card,
                    home_content,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                scroll=ft.ScrollMode.AUTO,
            ),
        )
    )

    token = page.client_storage.get("gymve_token")
    base_stored = page.client_storage.get("gymve_api_base") or DEFAULT_API
    if token:

        async def restore() -> None:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"{base_stored.rstrip('/')}/api/v1/me",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                if resp.status_code == 200:
                    go_home(resp.json())
            except httpx.RequestError:
                pass

        page.run_task(restore)


if __name__ == "__main__":
    ft.app(target=main)
