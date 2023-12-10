from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    debug: bool

    bot_token: str
    bot_admin_chats: list

    txt_help: str = (
        "/help 输出本帮助\n"
        "/pin 回复一条消息，置顶该消息\n"
        "/unpin 回复一条消息，取消置顶该消息\n"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


config = Settings()

if __name__ == "__main__":
    print(config.dict())
