"""fix_topology_snapshot_timestamps

Revision ID: 4dfc95ddc5e4
Revises: bb86b6f8fd55
Create Date: 2026-01-11 16:45:06.826879

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4dfc95ddc5e4'
down_revision: Union[str, None] = 'bb86b6f8fd55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 更新所有 NULL 值为当前时间
    op.execute("""
        UPDATE topology_snapshots 
        SET created_at = CURRENT_TIMESTAMP 
        WHERE created_at IS NULL
    """)
    
    op.execute("""
        UPDATE topology_snapshots 
        SET updated_at = CURRENT_TIMESTAMP 
        WHERE updated_at IS NULL
    """)
    
    # 2. 修改列为 NOT NULL 并设置服务器默认值
    op.alter_column('topology_snapshots', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=sa.text('CURRENT_TIMESTAMP'))
    
    op.alter_column('topology_snapshots', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=sa.text('CURRENT_TIMESTAMP'))


def downgrade() -> None:
    # 恢复为可为 NULL
    op.alter_column('topology_snapshots', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)
    
    op.alter_column('topology_snapshots', 'updated_at',
                    existing_type=sa.DateTime(),
                    nullable=True,
                    server_default=None)
