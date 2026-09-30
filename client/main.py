"""Cliente GymVe (Flet) — login contra API FastAPI. APK Android vía `flet build apk`."""

import os

import flet as ft
import httpx

SPECIAL = set("!@#$%^&*()_+-=[]{}|;:',.<>?/`~\"\\")
DEFAULT_API = os.getenv("GYMVE_API_BASE_URL", "http://10.0.2.2:8000").rstrip("/")

ACCENT = "#7C3AED"
ACCENT_HOVER = "#6D28D9"
BG = "#FAF8FF"
TEXT = "#1A1625"
MUTED = "#5C5470"
PANEL_GRADIENT_START = "#EDE9FE"
PANEL_GRADIENT_END = "#FFEDD5"


def policy_ok(password: str) -> tuple[bool, str]:
    if len(password) < 10:
        return False, "La contraseña debe tener al menos 10 caracteres."
    if not any(c in SPECIAL for c in password):
        return False, "La contraseña debe incluir al menos un carácter especial."
    return True, ""


def main(page: ft.Page) -> None:
    page.title = "GymVe"
    page.bgcolor = BG
    page.padding = 24
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(font_family="Roboto")

    api_field = ft.TextField(
        label="URL del servidor API",
        value=page.client_storage.get("gymve_api_base") or DEFAULT_API,
        hint_text="http://192.168.1.10:8000",
        autofocus=False,
    )
    email_field = ft.TextField(
        label="Correo electrónico",
        keyboard_type=ft.KeyboardType.EMAIL,
        autocorrect=False,
    )
    password_field = ft.TextField(
        label="Contraseña",
        password=True,
        can_reveal_password=True,
    )
    error_text = ft.Text("", color="#A32D2D", size=13, visible=False)
    loading = ft.ProgressRing(visible=False, width=22, height=22)

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
                ft.Text(profile.get("display_name", ""), size=22, weight=ft.FontWeight.W_500),
                ft.Text(profile.get("email", ""), size=13, color=MUTED),
                ft.Container(
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[PANEL_GRADIENT_START, "#CFFAFE", PANEL_GRADIENT_END],
                    ),
                    border=ft.border.all(0.5, "#C4B5FD"),
                    border_radius=10,
                    padding=14,
                    content=ft.Text(
                        "Sesión iniciada. Aquí irán rutinas y progreso de GymVe.",
                        size=13,
                        color=TEXT,
                    ),
                ),
                ft.OutlinedButton("Cerrar sesión", on_click=logout_click),
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

    login_card.controls.extend(
        [
            ft.Row(
                [
                    ft.Container(
                        width=56,
                        height=56,
                        border_radius=10,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=["#7C3AED", "#DB2777", "#F97316"],
                        ),
                        alignment=ft.alignment.center,
                        content=ft.Text("GV", color=ft.Colors.WHITE, size=16, weight=ft.FontWeight.W_500),
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Text("GymVe", size=26, weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER, color=ACCENT),
            ft.Text("Tu gimnasio en familia", size=13, color=MUTED, text_align=ft.TextAlign.CENTER),
            api_field,
            email_field,
            password_field,
            ft.Text(
                "Mín. 10 caracteres y un símbolo especial (!@#…).",
                size=11,
                color="#A0A099",
            ),
            error_text,
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Entrar",
                        bgcolor=ACCENT,
                        color=ft.Colors.WHITE,
                        on_click=submit_login,
                        expand=True,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            elevation=4,
                            overlay_color=ACCENT_HOVER,
                        ),
                    ),
                    loading,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ]
    )

    page.add(
        ft.Column(
            [
                login_card,
                home_content,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
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
