"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Formik } from "formik";
import {
  Button,
  Card,
  Input,
  Label,
  TextField,
  FieldError,
  Spinner,
} from "@heroui/react";
import { LoginSchema } from "@/helpers/schemas";
import { loginWithForm } from "@/lib/auth.api";
import { createAuthCookie } from "@/actions/auth.action";

export function Login() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  return (
    <Card className="w-full max-w-md p-6">
      <Card.Header className="pb-2">
        <Card.Title className="text-2xl">Sign in to Colony</Card.Title>
        <Card.Description>Manage your expenses</Card.Description>
      </Card.Header>
      <Card.Content>
        <Formik
          initialValues={{ username: "", password: "" }}
          validationSchema={LoginSchema}
          onSubmit={async (values, { setSubmitting }) => {
            setError(null);
            const result = await loginWithForm(
              values.username,
              values.password,
            );
            if (result.success) {
              await createAuthCookie((result.data as any).access_token);
              router.replace("/cycles");
            } else {
              setError(result.error.message);
            }
            setSubmitting(false);
          }}
        >
          {({
            values,
            errors,
            touched,
            setFieldValue,
            handleSubmit,
            isSubmitting,
          }) => (
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <TextField
                isInvalid={!!errors.username && !!touched.username}
                value={values.username}
                onChange={(v) => setFieldValue("username", v)}
              >
                <Label>Username</Label>
                <Input type="text" autoComplete="username" />
                {touched.username && errors.username && (
                  <FieldError>{errors.username}</FieldError>
                )}
              </TextField>
              <TextField
                isInvalid={!!errors.password && !!touched.password}
                value={values.password}
                onChange={(v) => setFieldValue("password", v)}
              >
                <Label>Password</Label>
                <Input type="password" autoComplete="current-password" />
                {touched.password && errors.password && (
                  <FieldError>{errors.password}</FieldError>
                )}
              </TextField>
              {error && <p className="text-sm text-red-500">{error}</p>}
              <Button
                type="submit"
                variant="primary"
                fullWidth
                isDisabled={isSubmitting}
              >
                {isSubmitting ? <Spinner size="sm" /> : "Sign In"}
              </Button>
            </form>
          )}
        </Formik>
      </Card.Content>
    </Card>
  );
}
