from datetime import datetime

from app.models.base import BaseDBModel
from tortoise import fields
from pydantic import BaseModel, ConfigDict
from tortoise.contrib.pydantic import pydantic_model_creator

# ========================================
# 说明: 数据模型
# ========================================


# TODO：================= 用户 & 用户组 =======================#

class User(BaseDBModel):
    """
    TODO 示例：用户
    """
    username = fields.CharField(max_length=20, unique=True, description="用户名")
    nickname = fields.CharField(max_length=50, null=True, description="昵称")
    email = fields.CharField(max_length=255, null=True, description="联系邮箱")
    weixin_id= fields.CharField(max_length=255, null=True, description="微信id")
    weixin_user= fields.CharField(max_length=255, null=True, description="微信用户")
    password = fields.CharField(max_length=128, description="密码")
    phone = fields.CharField(max_length=20, null=True,description="手机号")
    last_login = fields.DatetimeField(null=True, description="上次登录")
    is_active = fields.BooleanField(default=True, description="是否活跃")
    is_superuser = fields.BooleanField(default=False, description="是否管理员")
    is_confirmed = fields.BooleanField(default=False, description="是否确认")
    avatar = fields.CharField(max_length=512, null=True, description="头像")
    group = fields.ForeignKeyField('models.Org', related_name='users')

    class Meta:
        table = "users"
        table_description = "用户"


class HunterProfile(BaseDBModel):
    """
    猎头个人信息表
    """
    user = fields.OneToOneField("models.User", related_name="hunter_profile")
    company = fields.CharField(max_length=200, null=True)
    title = fields.CharField(max_length=100, null=True)
    specialization = fields.CharField(max_length=200, null=True)  # 专注领域
    contact_info = fields.JSONField(null=True)  # 联系方式

    class Meta:
        table = "hunter_profiles"

class Org(BaseDBModel):
    """
    TODO 示例：用户组
    """
    name = fields.CharField(max_length=50, unique=True)
    class Meta:
        table = "orgs"
        table_description = "用户组"


class Resume(BaseDBModel):
    """
    简历主表
    """
    user = fields.ForeignKeyField("models.User", related_name="resumes")
    original_filename = fields.CharField(max_length=255)
    file_path = fields.CharField(max_length=500)
    file_type = fields.CharField(max_length=10)  # txt, pdf, doc, docx
    raw_text = fields.TextField()
    analysis_status = fields.CharField(max_length=20, default='pending')  # pending, processing, completed, failed

    class Meta:
        table = "resumes"


class ContactInfo(BaseDBModel):
    """
    联系信息表
    """
    resume = fields.OneToOneField("models.Resume", related_name="contact_info")
    items = fields.JSONField(null=True)

    class Meta:
        table = "contact_info"


class BasicInfo(BaseDBModel):
    resume = fields.ForeignKeyField("models.Resume", related_name="basic_info")
    items = fields.JSONField(null=True)

    class Meta:
        table = "basic_info"
class WorkExperience(BaseDBModel):
    """
    工作经历表
    """
    resume = fields.ForeignKeyField("models.Resume", related_name="work_experiences")
    items = fields.JSONField(null=True)

    class Meta:
        table = "work_experiences"


class Education(BaseDBModel):
    resume = fields.ForeignKeyField("models.Resume", related_name="educations")
    items = fields.JSONField(null=True)

    class Meta:
        table = "educations"
class ProjectExperience(BaseDBModel):
    """
    项目经历表
    """
    resume = fields.ForeignKeyField("models.Resume", related_name="project_experiences")
    items = fields.JSONField(null=True)

    class Meta:
        table = "project_experiences"


class Skill(BaseDBModel):
    """
    技能表
    """
    resume = fields.ForeignKeyField("models.Resume", related_name="skills")
    items = fields.JSONField()

    class Meta:
        table = "skills"


class AIEvaluation(BaseDBModel):
    resume = fields.ForeignKeyField("models.Resume", related_name="ai_evaluations")
    score = fields.FloatField()  # 综合评分
    strengths = fields.TextField()  # 优势分析
    improvements = fields.TextField()  # 改进建议
    job_fit = fields.TextField()  # 岗位匹配度分析
    generated_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "ai_evaluations"


class AnalysisResult(BaseDBModel):
    """
    分析结果表
    """
    resume = fields.OneToOneField("models.Resume", related_name="analysis_result")
    career_timeline = fields.TextField()
    project_summary = fields.TextField()
    core_skills = fields.JSONField()
    analysis_time = fields.DatetimeField(default=datetime.utcnow)

    class Meta:
        table = "analysis_results"


# ========================================
# 猎头功能相关模型
# ========================================

class JobPosting(BaseDBModel):
    """
    岗位发布表
    """
    hunter = fields.ForeignKeyField("models.User", related_name="job_postings")
    title = fields.CharField(max_length=200)
    company = fields.CharField(max_length=200)
    location = fields.CharField(max_length=100, null=True)
    salary_range = fields.CharField(max_length=100, null=True)
    experience_required = fields.CharField(max_length=100, null=True)
    education_required = fields.CharField(max_length=100, null=True)
    job_description = fields.TextField()
    required_skills = fields.JSONField()  # 所需技能列表
    benefits = fields.JSONField(null=True)  # 福利待遇
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "job_postings"


class ResumeAccess(BaseDBModel):
    """
    简历访问权限表
    """
    hunter = fields.ForeignKeyField("models.User", related_name="resume_accesses")
    resume = fields.ForeignKeyField("models.Resume", related_name="accesses")
    access_level = fields.CharField(max_length=20, default="view")  # view, edit, full

    class Meta:
        table = "resume_accesses"


class JobMatch(BaseDBModel):
    """
    岗位匹配结果表
    """
    hunter = fields.ForeignKeyField("models.User", related_name="job_matches")
    job_posting = fields.ForeignKeyField("models.JobPosting", related_name="matches")
    resume = fields.ForeignKeyField("models.Resume", related_name="job_matches")
    match_score = fields.FloatField()  # 匹配分数 0-100
    matched_skills = fields.JSONField()  # 匹配的技能
    missing_skills = fields.JSONField()  # 缺失的技能
    notes = fields.TextField(null=True)

    class Meta:
        table = "job_matches"

# 用户相关
User_Pydantic = pydantic_model_creator(User, name="User", exclude=("password_hash",))
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)

# 猎头资料
HunterProfile_Pydantic = pydantic_model_creator(HunterProfile, name="HunterProfile")
HunterProfileIn_Pydantic = pydantic_model_creator(HunterProfile, name="HunterProfileIn", exclude_readonly=True)

# 岗位发布
JobPosting_Pydantic = pydantic_model_creator(JobPosting, name="JobPosting")
JobPostingIn_Pydantic = pydantic_model_creator(JobPosting, name="JobPostingIn", exclude_readonly=True)

# 简历相关
Resume_Pydantic = pydantic_model_creator(Resume, name="Resume")
ContactInfo_Pydantic = pydantic_model_creator(ContactInfo, name="ContactInfo")
WorkExperience_Pydantic = pydantic_model_creator(WorkExperience, name="WorkExperience")
ProjectExperience_Pydantic = pydantic_model_creator(ProjectExperience, name="ProjectExperience")
Skill_Pydantic = pydantic_model_creator(Skill, name="Skill")
AnalysisResult_Pydantic = pydantic_model_creator(AnalysisResult, name="AnalysisResult")

# 简历访问权限
ResumeAccess_Pydantic = pydantic_model_creator(ResumeAccess, name="ResumeAccess")
ResumeAccessIn_Pydantic = pydantic_model_creator(ResumeAccess, name="ResumeAccessIn", exclude_readonly=True)

# 岗位匹配
JobMatch_Pydantic = pydantic_model_creator(JobMatch, name="JobMatch")
JobMatchIn_Pydantic = pydantic_model_creator(JobMatch, name="JobMatchIn", exclude_readonly=True)

BasicInfo_Pydantic = pydantic_model_creator(BasicInfo, name="BasicInfo")
BasicInfoIn_Pydantic = pydantic_model_creator(BasicInfo, name="BasicInfoIn", exclude_readonly=True)

Education_Pydantic = pydantic_model_creator(Education, name="Education")
EducationIn_Pydantic = pydantic_model_creator(Education, name="EducationIn", exclude_readonly=True)

AIEvaluation_Pydantic = pydantic_model_creator(AIEvaluation, name="AIEvaluation")
AIEvaluationIn_Pydantic = pydantic_model_creator(AIEvaluation, name="AIEvaluationIn", exclude_readonly=True)