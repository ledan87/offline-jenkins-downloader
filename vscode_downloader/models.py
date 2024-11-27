from __future__ import annotations
from typing import Self

from django.db import models

class VsixPackage(models.Model):
    def __init__(self: Self, publisher: str, extension: str, version: str, target: str | None = None):
        self.publisher = publisher
        self.extension = extension
        self.version = version
        self.target = target

    def get_url(self: Self) -> str:
        url = (
            f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/"
            f"{self.publisher}/vsextensions/{self.extension}/{self.version}/vspackage"
        )
        if self.target:
            url += f"?targetPlatform={self.target}"
        return url

    def get_vsix_name(self: Self) -> str:
        return f"{self.publisher}.{self.extension}-{self.version}.vsix"