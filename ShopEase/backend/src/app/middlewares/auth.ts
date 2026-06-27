import { NextFunction, Request, Response } from "express";
import ApiError from "../errors/ApiError";
import { jwtHelpers } from "../../helpers/jwtHelpers";
import config from "../../config";
import { Secret } from "jsonwebtoken";

const auth = (...roles: string[]) => {
  return async (
    req: Request & { user?: any },
    res: Response,
    next: NextFunction
  ) => {
    try {
      const token = req.headers.authorization

      if(!token) throw new ApiError(401, "You are not authorized")

      const verifiedUser = jwtHelpers.verifyToken(token, config.jwt.jwt_secret as Secret)

      
      req.user = verifiedUser

      if(roles.length && !roles.includes(verifiedUser.role)) throw new ApiError(403, "Forbidden")

      next();
    } catch (error) {
      next(error);
    }
  };
};

export default auth;
