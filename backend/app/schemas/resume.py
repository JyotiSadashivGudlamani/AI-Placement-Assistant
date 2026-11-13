"""
Pydantic schemas for Module 4: Resume Analyser.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    github: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None


class ExtractedSkills(BaseModel):
    languages: List[str] = []
    frameworks_and_libraries: List[str] = []
    databases: List[str] = []
    tools_and_platforms: List[str] = []
    all_skills: List[str] = []


class EducationItem(BaseModel):
    degree: str
    institution: Optional[str] = None
    year: Optional[str] = None
    gpa_or_percentage: Optional[str] = None


class ProjectItem(BaseModel):
    title: str
    technologies: List[str] = []
    description: Optional[str] = None
    highlights: List[str] = []


class ResumeAnalysisResponse(BaseModel):
    resume_id: str
    filename: str
    file_type: str
    contact_info: ContactInfo
    skills: ExtractedSkills
    education: List[EducationItem]
    projects: List[ProjectItem]
    strengths: List[str]
    missing_information: List[str]
    improvement_suggestions: List[str]
    raw_text_length: int
    uploaded_at: str


class ResumeSummaryItem(BaseModel):
    resume_id: str
    filename: str
    uploaded_at: str
    skills_count: int
    education_count: int
    projects_count: int


class ResumeListResponse(BaseModel):
    total: int
    resumes: List[ResumeSummaryItem]
