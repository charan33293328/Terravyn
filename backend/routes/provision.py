import secrets
import string
import os
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.connection import get_db
from models.domain import Device
from schemas.domain import DeviceProvisionRequest, DeviceProvisionResponse

router = APIRouter()


