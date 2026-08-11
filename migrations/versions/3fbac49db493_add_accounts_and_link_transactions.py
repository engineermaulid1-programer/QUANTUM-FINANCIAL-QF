from alembic import op
import sqlalchemy as sa


revision = "3fbac49db493"

down_revision = "7074755fd7dc"

branch_labels = None

depends_on = None


def upgrade():

    with op.batch_alter_table(
        "transactions",
        schema=None
    ) as batch_op:

        batch_op.add_column(
            sa.Column(
                "account_id",
                sa.Integer(),
                nullable=True
            )
        )

        batch_op.create_foreign_key(
            "fk_transactions_account_id_accounts",
            "accounts",
            ["account_id"],
            ["id"]
        )


def downgrade():

    with op.batch_alter_table(
        "transactions",
        schema=None
    ) as batch_op:

        batch_op.drop_constraint(
            "fk_transactions_account_id_accounts",
            type_="foreignkey"
        )

        batch_op.drop_column(
            "account_id"
        )